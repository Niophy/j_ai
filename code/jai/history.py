"""Evaluation history: every saved grading, kept in one local SQLite file (v2).

Why: run files answer "what happened in this run"; history answers "what is
happening over time", which is what the KPIs need (learning gain across
attempts, turnaround, how often the marking-scheme check overrides the judge).

Local only, standard library only. The file holds students' answers, so it is
personal data: `purge(before=...)` deletes old rows for a retention policy
(see docs/GOVERNANCE.md). JAI_HISTORY_DB moves the file; JAI_HISTORY=0 turns
recording off.
"""

import hashlib
import json
import os
import sqlite3
import statistics
import time
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[1] / "runs" / "history.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS gradings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at   REAL    NOT NULL,
    run_id        TEXT    NOT NULL,
    source        TEXT    NOT NULL,
    student       TEXT,
    case_id       TEXT    NOT NULL,
    case_type     TEXT,
    status        TEXT    NOT NULL,
    score         REAL,
    verdict       TEXT,
    judge_verdict TEXT,
    overridden    INTEGER NOT NULL DEFAULT 0,
    latency_s     REAL,
    provider      TEXT,
    answer_sha256 TEXT,
    answer        TEXT
);
CREATE INDEX IF NOT EXISTS idx_gradings_student_case ON gradings (student, case_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_gradings_recorded ON gradings (recorded_at);
"""


def db_path():
    return Path(os.getenv("JAI_HISTORY_DB") or DEFAULT_DB)


def enabled():
    return os.getenv("JAI_HISTORY", "1") != "0"


def connect(path=None):
    p = Path(path) if path else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _score(result):
    s = result.get("score")
    if isinstance(s, bool) or not isinstance(s, (int, float)):
        return None
    return float(s)


def record(results, run_id, source="run", student=None, provider=None, path=None):
    """Store one row per graded result. Returns the number of rows written."""
    if not enabled() or not results:
        return 0
    rows = []
    for r in results:
        res = r.get("result") or {}
        check = res.get("rubric_check") or {}
        answer = r.get("answer") or ""
        rows.append((
            r.get("timestamp") or time.time(), str(run_id), source, student,
            r.get("case_id"), r.get("type"), r.get("status") or "graded",
            _score(res), (str(res.get("verdict")).lower() if res.get("verdict") is not None else None),
            check.get("judge_verdict"), 1 if check.get("overridden") else 0,
            r.get("latency_seconds"), provider,
            hashlib.sha256(answer.encode("utf-8")).hexdigest() if answer else None, answer,
        ))
    with connect(path) as conn:
        conn.executemany(
            "INSERT INTO gradings (recorded_at, run_id, source, student, case_id, case_type, status, score, verdict,"
            " judge_verdict, overridden, latency_s, provider, answer_sha256, answer)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def import_run_files(runs_dir, path=None):
    """Backfill history from existing run_*.json files; skips runs already recorded.

    Returns (runs_imported, gradings_imported). Run files are never modified.
    """
    runs_dir = Path(runs_dir)
    with connect(path) as conn:
        known = {row[0] for row in conn.execute("SELECT DISTINCT run_id FROM gradings")}
    runs = gradings = 0
    for f in sorted(runs_dir.glob("run_*.json")):
        if f.stem in known:
            continue
        try:
            data = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        results = data.get("results") or []
        n = record(results, run_id=f.stem, source="import", student=data.get("student"),
                   provider=data.get("provider"), path=path)
        runs += 1 if n else 0
        gradings += n
    # Student-agent records: each graded submission becomes a row under one
    # student name per agent model, the same shape save_record writes live.
    for f in sorted(runs_dir.rglob("agent_*.json")):
        if f.stem in known:
            continue
        try:
            rec = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rows = [{
            "timestamp": rec.get("timestamp"), "case_id": rec.get("case_id"), "type": rec.get("type"),
            "status": a.get("status"), "latency_seconds": a.get("latency_seconds"), "answer": a.get("answer"),
            "result": {"score": a.get("score"), "verdict": a.get("verdict"),
                       "rubric_check": {"judge_verdict": a.get("judge_verdict", a.get("verdict")),
                                        "overridden": a.get("judge_verdict", a.get("verdict")) != a.get("verdict")}},
        } for a in rec.get("attempts") or []]
        n = record(rows, run_id=f.stem, source="import-agent", student=f"agent:{rec.get('student')}",
                   provider=rec.get("judge"), path=path)
        runs += 1 if n else 0
        gradings += n
    return runs, gradings


def recent(limit=20, student=None, path=None):
    q = "SELECT * FROM gradings"
    args = []
    if student:
        q += " WHERE student = ?"
        args.append(student)
    q += " ORDER BY recorded_at DESC, id DESC LIMIT ?"
    args.append(int(limit))
    with connect(path) as conn:
        return [dict(row) for row in conn.execute(q, args)]


def purge(before, path=None):
    """Delete rows recorded before `before` (epoch seconds). Returns rows deleted."""
    with connect(path) as conn:
        cur = conn.execute("DELETE FROM gradings WHERE recorded_at < ?", (float(before),))
        return cur.rowcount


def _load_labels(labels):
    """Instructor verdicts: {"<run_id>:<case_id>": "pass"|"fail"} or a path to such a JSON file."""
    if labels is None:
        return None
    if isinstance(labels, (str, Path)):
        with open(labels, "r", encoding="utf-8") as f:
            labels = json.load(f)
    return {k: str(v).lower() for k, v in labels.items()}


def kpis(student=None, since=None, labels=None, path=None):
    """Compute the v2 KPIs from history.

    - feedback turnaround: median and 90th-percentile seconds per model grading
    - judge alignment: share of judge "pass" verdicts the marking-scheme check overrode
    - learning gain: per (student, case) with 2+ graded attempts, last score minus first
    - reliability: share of gradings that ended in a provider error
    - instructor agreement: share of labelled gradings where JADE's verdict matches
      the instructor's (only when labels are given; otherwise reported as not measured)
    """
    q = "SELECT * FROM gradings WHERE 1=1"
    args = []
    if student:
        q += " AND student = ?"
        args.append(student)
    if since is not None:
        q += " AND recorded_at >= ?"
        args.append(float(since))
    q += " ORDER BY recorded_at, id"
    with connect(path) as conn:
        rows = [dict(r) for r in conn.execute(q, args)]

    graded = [r for r in rows if r["status"] == "graded"]
    latencies = sorted(r["latency_s"] for r in graded if r["latency_s"])
    judge_pass = [r for r in graded if r["judge_verdict"] == "pass"]

    attempts = {}
    for r in graded:
        if r["student"] and r["score"] is not None:
            attempts.setdefault((r["student"], r["case_id"]), []).append(r["score"])
    gains = {f"{s}:{c}": round(v[-1] - v[0], 2) for (s, c), v in attempts.items() if len(v) >= 2}

    label_map = _load_labels(labels)
    agreement = None
    labelled = 0
    if label_map:
        matches = 0
        for r in graded:
            key = f"{r['run_id']}:{r['case_id']}"
            if key in label_map:
                labelled += 1
                matches += int(label_map[key] == r["verdict"])
        agreement = round(matches / labelled, 3) if labelled else None

    def pct(values, p):
        if not values:
            return None
        k = max(0, min(len(values) - 1, round(p * (len(values) - 1))))
        return round(values[k], 1)

    return {
        "gradings_total": len(rows),
        "gradings_graded": len(graded),
        "students": len({r["student"] for r in rows if r["student"]}),
        "pass_rate": round(sum(r["verdict"] == "pass" for r in graded) / len(graded), 3) if graded else None,
        "turnaround_median_s": round(statistics.median(latencies), 1) if latencies else None,
        "turnaround_p90_s": pct(latencies, 0.9),
        "judge_override_rate": round(sum(r["overridden"] for r in judge_pass) / len(judge_pass), 3) if judge_pass else None,
        "provider_error_rate": round(sum(r["status"] == "provider_error" for r in rows) / len(rows), 3) if rows else None,
        "learning_gain_mean": round(statistics.mean(gains.values()), 2) if gains else None,
        "learning_gain_by_student_case": gains,
        "instructor_agreement": agreement if label_map else "not measured: needs instructor labels",
        "instructor_labelled": labelled,
    }
