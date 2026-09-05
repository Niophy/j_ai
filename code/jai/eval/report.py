"""Turn a saved evaluation run into a human-readable markdown report.

Usage:
    python -m jai.eval.report runs/run_<timestamp>.json
    (no argument: reports the newest run; output lands in outputs/)
"""

import sys
import time
from pathlib import Path

from jai.eval.runner import load_cases
from jai.eval.scorers import load_run, newest_run, summarize, _status

OUTPUTS_DIR = Path(__file__).resolve().parents[2] / "outputs"

# Keys rendered specially; every other list-valued result key (missing_points,
# design_flaws, incorrect_claims, ...) is rendered generically, so per-template
# schema differences need no code changes here.
CORE_KEYS = {"score", "verdict", "reason", "error", "raw_output"}


def _case_text(case):
    if not case:
        return None
    inp = case.get("input", {})
    return inp.get("scenario") or inp.get("question")


def build_report(run: dict) -> str:
    try:
        cases = {c["id"]: c for c in load_cases().get("cases", [])}
    except Exception:
        cases = {}

    s = summarize(run)
    lines = ["# J_AI Evaluation Report", ""]
    lines.append(f"Course: {s.get('course')} | Provider: {s.get('provider')} | "
                 f"Generated: {time.strftime('%Y-%m-%d %H:%M')}")
    lines += ["", "## Scoreboard", "", "| Metric | Value |", "|---|---|"]
    for key, value in s.items():
        if key in ("course", "provider", "average_by_type"):
            continue
        lines.append(f"| {key.replace('_', ' ')} | {value} |")
    for case_type, avg in (s.get("average_by_type") or {}).items():
        lines.append(f"| average: {case_type} | {avg} |")
    lines.append("")

    for record in run.get("results", []):
        result = record.get("result", {})
        status = _status(record)
        verdict = str(result.get("verdict", "?")).upper()
        lines.append(f"## {record.get('case_id')} | {record.get('type')} | "
                     f"{result.get('score')}/10 {verdict} ({status})")
        lines.append("")

        question = _case_text(cases.get(record.get("case_id")))
        if question:
            lines += [f"**Question:** {question}", ""]

        answer = record.get("answer")
        if answer and answer.strip():
            lines.append("**Answer:**")
            lines.append("")
            for answer_line in answer.strip().splitlines():
                lines.append(f"> {answer_line}")
            lines.append("")

        if result.get("reason"):
            lines += [f"**Reason:** {result['reason']}", ""]
        if result.get("error"):
            lines += [f"**Error:** {result['error']}", ""]

        for key, value in result.items():
            if key in CORE_KEYS or not isinstance(value, list) or not value:
                continue
            lines.append(f"**{key.replace('_', ' ').title()}:**")
            for item in value:
                lines.append(f"- {item}")
            lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else newest_run()
    if not path or not path.exists():
        print("No run file found. Pass a path or create one via eval mode.")
        sys.exit(1)

    OUTPUTS_DIR.mkdir(exist_ok=True)
    out_path = OUTPUTS_DIR / (path.stem.replace("run_", "report_") + ".md")
    out_path.write_text(build_report(load_run(path)), encoding="utf-8")
    print(f"Report written to {out_path}")


if __name__ == "__main__":
    main()
