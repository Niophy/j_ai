"""v2.1 regression: re-score the stored v2 judge outputs for Test A and Test B with the points-based rule.

The judge prompt is unchanged in v2.1 and the rule never touches the verdict, so the stored
judge outputs are re-scored instead of re-graded. Output: runs/v21_regression.json
"""
import copy, glob, json, sys
sys.path.insert(0, "/home/j/J_AI")
from jai.eval.runner import apply_points_score, load_cases

PRED = {"a": {"REQ_001": "pass", "REQ_002": "fail", "LOG_001": "pass", "PROT_001": "pass", "SEC_001": "fail"},
        "b": {k: "fail" for k in ("REQ_001", "REQ_002", "LOG_001", "PROT_001", "SEC_001")}}
cases = {c["id"]: c for c in load_cases()["cases"]}

latest = {}
for f in sorted(glob.glob("/home/j/J_AI/runs/run_*.json")):
    d = json.load(open(f))
    if d.get("course") != "v2_regression":
        continue
    key = d.get("version")
    latest[key] = (f, d["results"][0])

out, hits = {}, 0
print(" test case      v2 judge score  v2.1 score  verdict  predicted  match")
for key in sorted(latest):
    f, rec = latest[key]
    t, c = key.split(":")
    r = apply_points_score(cases[c], copy.deepcopy(rec["result"]))
    ok = r["verdict"] == PRED[t][c]
    hits += ok
    out[key] = {"source_run": f.rsplit("/", 1)[1], "v2_score": rec["result"].get("score"), "v21_score": r["score"],
                "verdict": r["verdict"], "predicted": PRED[t][c], "match": ok, "score_check": r.get("score_check")}
    print(f"  {t.upper()}   {c:9} {rec['result'].get('score')!s:>9}       {r['score']:>6}     {r['verdict']:7}  {PRED[t][c]:9}  {'MATCH' if ok else 'MISS'}")
print(f"\n predictions matched {hits} of {len(out)}")
json.dump(out, open("/home/j/J_AI/runs/v21_regression.json", "w"), indent=2)
