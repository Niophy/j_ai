import json
import sys
import time
from pathlib import Path

from src.core.provider_factory import get_provider
from src.core.jsonx import extract_first_json_object
from jai.eval.templates import TEMPLATES


CASES_PATH = Path(__file__).parent / "cases.json"
RUNS_DIR = Path(__file__).resolve().parents[2] / "runs"

# Anything shorter than this is not gradeable material; the judge never sees it.
# 20 chars blocks blanks and throwaways ("idk", "no idea") while letting any
# genuine attempt through. Found 2026-09-03: the model scored blank answers 8/10.
MIN_ANSWER_CHARS = 20

# Every result carries exactly one status, set here and only here.
# Consumers (scorers.py, cli.py) read status instead of sniffing for keys.
STATUS_GRADED = "graded"                  # the model produced a valid verdict
STATUS_GUARD_REJECTED = "guard_rejected"  # input guard refused; model never called
STATUS_PROVIDER_ERROR = "provider_error"  # model called but returned no usable JSON


def load_cases():
    with open(CASES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(template_key, case, student_answer):
    template = TEMPLATES[template_key]
    case_type = case["type"]

    if case_type in ("requirements_analysis", "logical_design", "security_strategy"):
        return template.format(
            scenario=case["input"]["scenario"],
            student_answer=student_answer,
        )

    if case_type == "protocol_selection":
        return template.format(
            question=case["input"]["question"],
            student_answer=student_answer,
        )

    raise ValueError(f"Unknown case type: {case_type}")


def _wrap(case, latency, status, result):
    return {
        "timestamp": time.time(),
        "case_id": case["id"],
        "type": case["type"],
        "status": status,
        "latency_seconds": latency,
        "result": result,
    }


def _parse_verdict(text):
    """Return the verdict dict if text contains one valid verdict object, else None."""
    for candidate_text in (text, extract_first_json_object(text)):
        if not candidate_text:
            continue
        try:
            candidate = json.loads(candidate_text)
        except Exception:
            continue
        if isinstance(candidate, dict) and "score" in candidate and "verdict" in candidate:
            return candidate
    return None


def run_single_case(case, provider, student_answer):
    answer = (student_answer or "").strip()
    if len(answer) < MIN_ANSWER_CHARS:
        return _wrap(case, 0.0, STATUS_GUARD_REJECTED, {
            "score": 0,
            "verdict": "fail",
            "reason": f"answer too short to grade (under {MIN_ANSWER_CHARS} characters)",
        })

    prompt = build_prompt(case["prompt_template"], case, student_answer)

    start = time.time()
    response = provider.generate_json(prompt)
    latency = time.time() - start

    parsed = _parse_verdict(response)
    if parsed is None:
        print(f"WARNING [{case['id']}]: no valid JSON verdict from provider.", file=sys.stderr)
        return _wrap(case, latency, STATUS_PROVIDER_ERROR, {
            "score": 0,
            "verdict": "fail",
            "error": "Invalid JSON returned",
            "raw_output": response,
        })

    return _wrap(case, latency, STATUS_GRADED, parsed)


def save_run(results, course=None, version=None, provider=None):
    """Single writer for run files; nanosecond names avoid same-second overwrites."""
    RUNS_DIR.mkdir(exist_ok=True)
    run_file = RUNS_DIR / f"run_{time.time_ns()}.json"
    with open(run_file, "w", encoding="utf-8") as f:
        json.dump(
            {"course": course, "version": version, "provider": provider, "results": results},
            f,
            indent=2,
            ensure_ascii=False,
        )
    return run_file


def run_all(student_answers: dict):
    data = load_cases()
    provider = get_provider()

    results = []
    for case in data.get("cases", []):
        answer = student_answers.get(case["id"], "")
        results.append(run_single_case(case, provider, answer))

    run_file = save_run(
        results,
        course=data.get("course"),
        version=data.get("version"),
        provider=str(type(provider).__name__),
    )
    print(f"Saved results to {run_file}")
    return results
