"""Student agent: the model sits the exam and J_AI's examiner is its only tool.

Job (spec 2026-09-10): given a case, write an answer that passes the examiner.
Draft, submit through submit_answer, read the verdict, revise on the cited
gaps, repeat until the verdict is pass or the submission budget is spent.

Why this is an agent and not another pipeline: the number of loops depends on
each verdict, which nobody can script in advance. Why it matters for J_AI: it
probes the judge from the student's side. If the agent passes by echoing the
verdict's wording back, the examiner is gameable; if it has to add real
content, the examiner holds.

The one rule that makes the experiment honest: the agent NEVER sees the case's
'expected' block. It gets the scenario and the verdict text, nothing else.

Usage:
    python -m jai.agent.student --case REQ_001
    python -m jai.agent.student --case PROT_001 --max-submissions 3

Exit codes: 0 = final answer passed, 1 = did not pass, 2 = runtime error.
"""

import argparse
import json
import sys
import time

from dotenv import load_dotenv

from jai.eval.runner import (
    RUNS_DIR,
    STATUS_GRADED,
    load_cases,
    provider_label,
    run_single_case,
)
from src.core.provider_factory import get_provider

load_dotenv()

OUTPUTS_DIR = RUNS_DIR.parent / "outputs"

# Guardrails. Steps count every model call; submissions count examiner calls.
# Both exist so a model that loops without submitting, or submits without
# ever finishing, still terminates.
DEFAULT_MAX_STEPS = 12
DEFAULT_MAX_SUBMISSIONS = 5
# A plain-text reply before the verdict is pass (or the budget is spent) is
# the model trying to finish without the examiner. It gets pushed back this
# many times; after that the run stops and says the student gave up.
# Found on the first live run 2026-09-10: the model answered at step 1 and
# never called the tool. Zero submissions, "final answer", loop happy. Wrong.
MAX_NUDGES = 2

TOOL_NAME = "submit_answer"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": TOOL_NAME,
            "description": (
                "Submit your exam answer to the examiner. Returns the score (0 to 10), "
                "the verdict (pass or fail) and the examiner's findings. You may submit "
                "several times; revise between submissions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The full text of your exam answer.",
                    }
                },
                "required": ["answer"],
            },
        },
    }
]

STUDENT_SYSTEM = """You are a student sitting a network design exam (ITE 402).

Your task: write the best exam answer you can to the scenario, then submit it
with the submit_answer tool. The examiner returns a score, a verdict and
findings. Read the findings, revise your answer to fix what is missing or
wrong, and submit again. Keep going until the verdict is pass or you run out
of submissions.

Rules:
- Always submit through the tool. An answer that was never submitted does not count.
- Write in English only.
- Write in prose or short structured sections, 150 to 350 words.
- Do not invent facts the scenario does not give (prices, vendors, standards).
- When the verdict is pass, or you cannot improve further, reply with plain
  text (no tool call) containing ONLY your final answer.
"""

# Verdict keys the student may see. Everything else in the examiner's result
# (raw model output, internal fields) stays hidden. The answer key in
# cases.json is never in the result at all, so it cannot leak here.
VISIBLE_VERDICT_KEYS = (
    "score", "verdict", "reason", "missing_points", "technical_errors",
    "design_flaws", "incorrect_claims", "missing_reasoning",
    "missing_controls", "risk_gaps", "strengths",
)


def find_case(case_id):
    for case in load_cases().get("cases", []):
        if case["id"] == case_id:
            return case
    return None


def case_text(case):
    return case["input"].get("scenario") or case["input"].get("question")


MISSING_KEYS = ("missing_points", "missing_reasoning", "missing_controls")


def strict_check(case, shown):
    """Apply the case's min_points threshold to the verdict, agent side.

    Found 2026-09-10 by this agent: the examiner listed 4 of 5 required points
    missing on LOG_001 and still said pass. Its verdict field ignores its own
    marking scheme. Until that post-check lives in the runner (Jaber's
    decision), --strict enforces it here so the revise loop can be tested.
    Only COUNTS are read from 'expected'; the student never sees the items.
    """
    expected = case.get("expected") or {}
    required = len(expected.get("must_include", [])) + len(expected.get("must_include_any", []))
    min_points = expected.get("min_points")
    if not min_points or not required:
        return shown
    allowed_missing = max(required - min_points, 0)
    missing = sum(len(shown.get(k, [])) for k in MISSING_KEYS)
    if missing > allowed_missing and str(shown.get("verdict", "")).lower() == "pass":
        shown["verdict"] = "fail"
        shown["note"] = (f"strict marking: {missing} required points missing, "
                         f"at most {allowed_missing} allowed for a pass. Cover the missing points.")
    return shown


def visible_verdict(outcome, case=None, strict=False):
    """What the student is allowed to read back from one grading."""
    result = outcome.get("result") or {}
    shown = {k: result[k] for k in VISIBLE_VERDICT_KEYS if k in result}
    shown["status"] = outcome.get("status")
    if outcome.get("status") != STATUS_GRADED:
        shown["note"] = "the examiner could not grade this submission; it still used one attempt"
    elif strict and case is not None:
        shown = strict_check(case, shown)
    return shown


def _tool_args(call):
    args = (call.get("function") or {}).get("arguments") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            args = {}
    return args


def run_student(case, student, judge, max_steps=DEFAULT_MAX_STEPS,
                max_submissions=DEFAULT_MAX_SUBMISSIONS, strict=False, log=print):
    """The agent loop. Returns a record of everything that happened."""
    messages = [
        {"role": "system", "content": STUDENT_SYSTEM},
        {"role": "user", "content": f"Exam question ({case['type']}):\n\n{case_text(case)}"},
    ]
    attempts = []
    passed = False
    final_answer = None
    stop_reason = "max_steps"
    steps = 0
    nudges = 0
    started = time.time()

    for step in range(1, max_steps + 1):
        steps = step
        reply = student.chat(messages, tools=TOOLS, options={"num_predict": 2048, "temperature": 0.3})
        assistant_msg = {"role": "assistant", "content": reply["content"], "tool_calls": reply["tool_calls"]}
        if reply.get("thinking"):
            # Thinking models expect their trace back in the history so a tool
            # call and its follow-up stay one line of reasoning.
            assistant_msg["thinking"] = reply["thinking"]
        messages.append(assistant_msg)

        if not reply["tool_calls"]:
            budget_spent = len(attempts) >= max_submissions
            if reply["content"] and (passed or budget_spent):
                final_answer = reply["content"]
                stop_reason = "final_answer"
                break
            if nudges >= MAX_NUDGES:
                stop_reason = "gave_up" if reply["content"] else "empty_reply"
                final_answer = reply["content"] or None  # kept as closing_text below
                break
            nudges += 1
            log(f"  step {step}: plain text before pass/budget, nudge {nudges}/{MAX_NUDGES}")
            messages.append({"role": "user", "content": (
                "You have not submitted this answer. Nothing counts until the examiner grades it. "
                f"Call {TOOL_NAME} now with your full answer in English.")})
            continue

        for call in reply["tool_calls"]:
            name = (call.get("function") or {}).get("name")

            if name != TOOL_NAME:
                # The model asked for a tool that does not exist. Refuse, log, continue.
                log(f"  step {step}: refused unknown tool '{name}'")
                messages.append({"role": "tool", "tool_name": str(name), "content": json.dumps(
                    {"error": f"unknown tool '{name}'. Only {TOOL_NAME} exists."})})
                continue

            if len(attempts) >= max_submissions:
                log(f"  step {step}: submission budget spent, asking for final answer")
                messages.append({"role": "tool", "tool_name": TOOL_NAME, "content": json.dumps(
                    {"error": "submission limit reached. Reply now with your final answer as plain text."})})
                continue

            answer = str(_tool_args(call).get("answer") or "")
            outcome = run_single_case(case, judge, answer)
            shown = visible_verdict(outcome, case, strict)
            attempt = {
                "n": len(attempts) + 1,
                "step": step,
                "status": outcome["status"],
                "score": outcome["result"].get("score"),
                "verdict": shown.get("verdict"),
                "judge_verdict": outcome["result"].get("verdict"),
                "latency_seconds": round(outcome["latency_seconds"], 2),
                "answer": answer,
                "verdict_shown": shown,
            }
            attempts.append(attempt)
            log(f"  attempt {attempt['n']}: score {attempt['score']} {attempt['verdict']} "
                f"({attempt['status']}, {attempt['latency_seconds']}s, {len(answer.split())} words)")

            if str(attempt["verdict"]).lower() == "pass":
                passed = True
                shown["note"] = "verdict is pass. Reply now with your final answer as plain text."
            messages.append({"role": "tool", "tool_name": TOOL_NAME, "content": json.dumps(shown)})

    # The final answer is always a GRADED submission, never the closing text.
    # Second live run 2026-09-10: after a pass the model rewrote its answer in
    # the plain-text reply, so the text it "handed in" was never examined.
    # The closing text is kept for the record; the best graded attempt counts.
    closing_text = final_answer
    best = max(attempts, key=lambda a: (a["score"] or 0), default=None)
    final_answer = best["answer"] if best is not None else None

    return {
        "kind": "student_agent",
        "timestamp": time.time(),
        "case_id": case["id"],
        "type": case["type"],
        "student": provider_label(student),
        "judge": provider_label(judge),
        "max_steps": max_steps,
        "max_submissions": max_submissions,
        "strict": strict,
        "steps": steps,
        "submissions": len(attempts),
        "nudges": nudges,
        "passed": passed,
        "stop_reason": stop_reason,
        "elapsed_seconds": round(time.time() - started, 1),
        "attempts": attempts,
        "final_answer": final_answer,
        "closing_text": closing_text,
        "transcript": messages,
    }


def save_record(record):
    RUNS_DIR.mkdir(exist_ok=True)
    path = RUNS_DIR / f"agent_{record['case_id']}_{time.time_ns()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return path


def write_markdown(record):
    """Readable transcript in outputs/: the score history and every attempt."""
    OUTPUTS_DIR.mkdir(exist_ok=True)
    path = OUTPUTS_DIR / f"agent_{record['case_id']}_{time.time_ns()}.md"
    lines = [
        f"# Student agent: {record['case_id']}",
        "",
        f"Student: `{record['student']}` · Judge: `{record['judge']}` · "
        f"steps {record['steps']}/{record['max_steps']} · "
        f"submissions {record['submissions']}/{record['max_submissions']} · "
        f"nudges {record['nudges']} · strict {record['strict']} · stop: {record['stop_reason']} · {record['elapsed_seconds']}s",
        "",
        "| attempt | score | verdict | judge said | status | words |",
        "|---|---|---|---|---|---|",
    ]
    for a in record["attempts"]:
        lines.append(f"| {a['n']} | {a['score']} | {a['verdict']} | {a['judge_verdict']} | {a['status']} | {len(a['answer'].split())} |")
    for a in record["attempts"]:
        lines += ["", f"## Attempt {a['n']}", "", a["answer"], "", "Examiner:", "",
                  "```json", json.dumps(a["verdict_shown"], indent=2, ensure_ascii=False), "```"]
    lines += ["", "## Final answer (best graded attempt)", "", record["final_answer"] or "(none)", ""]
    if record.get("closing_text") and record["closing_text"] != record["final_answer"]:
        lines += ["", "## Closing text (ungraded, for the record)", "", record["closing_text"], ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def main():
    parser = argparse.ArgumentParser(prog="jai.agent.student", description="student agent over J_AI's examiner")
    parser.add_argument("--case", required=True, help="case id from cases.json")
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument("--max-submissions", type=int, default=DEFAULT_MAX_SUBMISSIONS)
    parser.add_argument("--strict", action="store_true",
                        help="apply the case's min_points threshold to the verdict the student sees")
    parser.add_argument("--no-save", action="store_true", help="do not write run/outputs files")
    args = parser.parse_args()

    case = find_case(args.case)
    if case is None:
        print(f"Unknown case id: {args.case}", file=sys.stderr)
        return 2

    try:
        # Roles: JAI_JUDGE_MODEL / JAI_STUDENT_MODEL and *_THINK in .env pick
        # different models or thinking levels per side; unset means the default.
        judge = get_provider(role="judge")
        student = get_provider(role="student")

        print(f"[{case['id']}] student={provider_label(student)} judge={provider_label(judge)}")
        record = run_student(case, student, judge, args.max_steps, args.max_submissions, args.strict)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"stop={record['stop_reason']} steps={record['steps']} submissions={record['submissions']} "
          f"nudges={record['nudges']} strict={record['strict']} passed={record['passed']} "
          f"elapsed={record['elapsed_seconds']}s")
    if not args.no_save:
        print(f"Saved {save_record(record)}")
        print(f"Saved {write_markdown(record)}")
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
