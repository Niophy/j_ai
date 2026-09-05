"""Aggregate the results of an evaluation run into a scoreboard.

Usage:
    python -m jai.eval.scorers runs/run_1234567890.json
    (no argument: scores the newest run in runs/)
"""

import json
import sys
from pathlib import Path

from jai.eval.runner import RUNS_DIR


def load_run(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _status(record) -> str:
    """Read the record's status; infer it for runs saved before the field existed."""
    status = record.get("status")
    if status:
        return status
    return "provider_error" if "error" in record.get("result", {}) else "graded"


def _numeric_score(result):
    score = result.get("score", 0)
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return None
    return score


def summarize(run: dict) -> dict:
    results = run.get("results", [])

    graded = [r for r in results if _status(r) == "graded"]
    guarded = [r for r in results if _status(r) == "guard_rejected"]
    errors = [r for r in results if _status(r) == "provider_error"]

    # Guard rejections are academic zeros (an ungradeable submission counts
    # against the student); provider errors are infrastructure and never score.
    scorable = graded + guarded
    scores = []
    bad_scores = 0
    for r in scorable:
        s = _numeric_score(r["result"])
        if s is None:
            bad_scores += 1
        else:
            scores.append(s)

    passes = [r for r in scorable if str(r["result"].get("verdict", "")).lower() == "pass"]

    by_type: dict = {}
    for r in scorable:
        s = _numeric_score(r["result"])
        if s is not None:
            by_type.setdefault(r.get("type", "unknown"), []).append(s)

    model_latencies = [r.get("latency_seconds", 0) for r in graded]

    return {
        "course": run.get("course"),
        "provider": run.get("provider"),
        "cases_total": len(results),
        "cases_graded": len(graded),
        "cases_guard_rejected": len(guarded),
        "cases_provider_error": len(errors),
        "cases_bad_score_value": bad_scores,
        "average_score": round(sum(scores) / len(scores), 2) if scores else None,
        "pass_rate": round(len(passes) / len(scorable), 2) if scorable else None,
        "average_by_type": {t: round(sum(v) / len(v), 2) for t, v in by_type.items()},
        "avg_model_latency_seconds": round(
            sum(model_latencies) / len(model_latencies), 2
        ) if model_latencies else None,
    }


def newest_run() -> Path | None:
    runs = sorted(RUNS_DIR.glob("run_*.json"))
    return runs[-1] if runs else None


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else newest_run()
    if not path or not path.exists():
        print("No run file found. Pass a path or create one via eval mode.")
        sys.exit(1)

    summary = summarize(load_run(path))
    print(f"Scoreboard for {path.name}:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
