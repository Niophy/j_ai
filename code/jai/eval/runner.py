import json
import time
from pathlib import Path

from src.core.provider_factory import get_provider
from jai.eval.templates import TEMPLATES


CASES_PATH = Path(__file__).parent / "cases.json"
RUNS_DIR = Path(__file__).resolve().parents[2] / "runs"
RUNS_DIR.mkdir(exist_ok=True)

# Anything shorter than this is not gradeable material; the judge never sees it.
# 20 chars blocks blanks and throwaways ("idk", "no idea") while letting any
# genuine attempt through. Found 2026-09-03: the model scored blank answers 8/10.
MIN_ANSWER_CHARS = 20


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


def run_single_case(case, provider, student_answer):
    answer = (student_answer or "").strip()
    if len(answer) < MIN_ANSWER_CHARS:
        return {
            "timestamp": time.time(),
            "case_id": case["id"],
            "type": case["type"],
            "latency_seconds": 0.0,
            "result": {
                "score": 0,
                "verdict": "fail",
                "reason": "no answer submitted",
                "strengths": [],
                "missing_points": [],
                "technical_errors": [],
            },
        }

    prompt = build_prompt(case["prompt_template"], case, student_answer)

    start = time.time()

    if hasattr(provider, "generate_json"):
        response = provider.generate_json(prompt)
    else:
        response = provider.generate(prompt)

    latency = time.time() - start

    try:
        parsed = json.loads(response)

        if not isinstance(parsed, dict):
            raise ValueError("JSON is not an object")

        if "score" not in parsed or "verdict" not in parsed:
            raise ValueError("Missing required keys")

    except Exception:
        # Provider-level retries (JAI_JSON_RETRIES) are already exhausted here.
        print(f"WARNING [{case['id']}]: invalid JSON after retries — recorded as error, not scored.")
        parsed = {
            "score": 0,
            "verdict": "fail",
            "missing_points": [],
            "strengths": [],
            "error": "Invalid JSON returned",
            "raw_output": response,
        }

    return {
        "timestamp": time.time(),
        "case_id": case["id"],
        "type": case["type"],
        "latency_seconds": latency,
        "result": parsed,
    }


def run_all(student_answers: dict):
    data = load_cases()
    provider = get_provider()

    results = []
    for case in data.get("cases", []):
        answer = student_answers.get(case["id"], "")
        results.append(run_single_case(case, provider, answer))

    run_file = RUNS_DIR / f"run_{int(time.time())}.json"
    with open(run_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "course": data.get("course"),
                "version": data.get("version"),
                "provider": str(type(provider).__name__),
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Saved results to {run_file}")
    return results
