"""v2 regression: re-grade the registered v1.0 final-test answers with the v2 templates.
usage: PYTHONPATH=/home/j/J_AI python regress.py a:REQ_001 b:LOG_001 ...   |   summary
"""
import json, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("/home/j/J_AI/.env")
from jai.eval.runner import load_cases, run_single_case, save_run, provider_label
from src.core.provider_factory import get_provider

F = Path("/home/j/J_AI/runs/final_tests")
OUT = Path("/home/j/J_AI/runs/v2_regression.json")
PRED = {"a": {"REQ_001": "pass", "REQ_002": "fail", "LOG_001": "pass", "PROT_001": "pass", "SEC_001": "fail"},
        "b": {k: "fail" for k in ("REQ_001", "REQ_002", "LOG_001", "PROT_001", "SEC_001")}}
V1 = {"a": {"REQ_001": 9, "REQ_002": 2, "LOG_001": 8, "PROT_001": 9, "SEC_001": 2},
      "b": {"REQ_001": 3, "REQ_002": 1, "LOG_001": 1, "PROT_001": 1, "SEC_001": 1}}

if sys.argv[1:] == ["summary"]:
    res = json.load(open(OUT)); hits = 0
    print(" test case      v1 score  v2 score  v2 verdict  predicted  match")
    for key, r in sorted(res.items()):
        t, c = key.split(":"); p = PRED[t][c]; ok = r["verdict"] == p; hits += ok
        print(f"  {t.upper()}   {c:9} {V1[t][c]:>6}    {r['score']!s:>6}    {r['verdict']:9}  {p:9}  {'MATCH' if ok else 'MISS'}  ({r['template']})")
    print(f"\n predictions matched {hits} of {len(res)}")
    sys.exit(0)

cases = {c["id"]: c for c in load_cases()["cases"]}
judge = get_provider(role="judge")
res = json.load(open(OUT)) if OUT.exists() else {}
for key in sys.argv[1:]:
    t, c = key.split(":")
    answer = json.load(open(F / f"answers_test_{t}.json"))[c]
    out = run_single_case(cases[c], judge, answer)
    save_run([out], course="v2_regression", version=key, provider=provider_label(judge), student=f"regression:{t}", source="regression")
    r = out["result"]
    res[key] = {"score": r.get("score"), "verdict": r.get("verdict"), "template": out.get("template"), "seconds": round(out["latency_seconds"], 1)}
    json.dump(res, open(OUT, "w"), indent=2)
    print(f"{t.upper()} {c}: {r.get('score')}/10 {r.get('verdict')}  (v1 was {V1[t][c]}, predicted {PRED[t][c]}, {out['latency_seconds']:.0f} s)", flush=True)
