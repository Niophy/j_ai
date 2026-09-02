"""Aggregate the results of an evaluation run into a scoreboard.

Usage:
    python -m jai.eval.scorers runs/run_1234567890.json
    (no argument: scores the newest run in runs/)
"""

import json
import sys
from pathlib import Path

RUNS_DIR = Path(__file__).resolve().parents[2] / "runs"


def load_run(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def summarize(run: dict) -> dict:
    results = run.get("results", [])
    scored = [r for r in results if "error" not in r.get("result", {})]
    invalid = [r for r in results if "error" in r.get("result", {})]

    scores = [r["result"].get("score", 0) for r in scored]
    passes = [r for r in scored if str(r["result"].get("verdict", "")).lower() == "pass"]

    by_type: dict = {}
    for r in scored:
        t = r.get("type", "unknown")
        by_type.setdefault(t, []).append(r["result"].get("score", 0))

    return {
        "course": run.get("course"),
        "provider": run.get("provider"),
        "cases_total": len(results),
        "cases_scored": len(scored),
        "cases_invalid_json": len(invalid),
        "average_score": round(sum(scores) / len(scores), 2) if scores else None,
        "pass_rate": round(len(passes) / len(scored), 2) if scored else None,
        "average_by_type": {t: round(sum(v) / len(v), 2) for t, v in by_type.items()},
        "avg_latency_seconds": round(
            sum(r.get("latency_seconds", 0) for r in results) / len(results), 2
        ) if results else None,
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
