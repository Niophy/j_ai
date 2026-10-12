"""JADE bias check (v2): same content, polished vs rough English, graded by the default judge.

Also measures GPU power draw during each grading (nvidia-smi, sampled every 0.5 s),
so the energy per grading can be reported in the cost note.
usage: PYTHONPATH=/home/j/J_AI python bias_check.py CASE:VERSION [CASE:VERSION ...]
       python bias_check.py summary
"""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv("/home/j/J_AI/.env")

from jai.eval.runner import load_cases, run_single_case, save_run, provider_label
from src.core.provider_factory import get_provider

HERE = Path(__file__).parent
OUT = HERE / "bias_results.json"
G, R, B, D, X = "\033[32m", "\033[31m", "\033[1m", "\033[2m", "\033[0m"


def power_watts():
    out = subprocess.run(["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out.splitlines()[0])
    except (ValueError, IndexError):
        return None


def grade(case, judge, answer):
    samples, stop = [], threading.Event()

    def sampler():
        while not stop.is_set():
            w = power_watts()
            if w is not None:
                samples.append(w)
            stop.wait(0.5)

    idle = power_watts()
    t = threading.Thread(target=sampler, daemon=True)
    t.start()
    out = run_single_case(case, judge, answer)
    stop.set()
    t.join()
    avg = sum(samples) / len(samples) if samples else None
    return out, idle, avg


def summary():
    res = json.load(open(OUT))
    print(f"{B} case       polished          rough             verdict same  gap  within 1{X}")
    ok_all = True
    for cid in ("REQ_001", "LOG_001", "PROT_001", "SEC_001"):
        p, r = res.get(f"{cid}:polished"), res.get(f"{cid}:rough")
        if not p or not r:
            print(f" {cid:10} incomplete"); ok_all = False; continue
        same = p["verdict"] == r["verdict"]
        gap = abs((p["score"] or 0) - (r["score"] or 0))
        ok = same and gap <= 1
        ok_all &= ok
        print(f" {cid:10} {p['score']}/10 {p['verdict']:4}        {r['score']}/10 {r['verdict']:4}        "
              f"{'yes' if same else 'NO':12}  {gap:>3}  {(G + 'yes') if ok else (R + 'NO')}{X}")
    e = [v["energy_wh"] for v in res.values() if v.get("energy_wh")]
    s = [v["seconds"] for v in res.values()]
    print(f"\n{B} bias check {'PASSED' if ok_all else 'FAILED'}{X}  |  gradings {len(res)}  |  "
          f"mean {sum(s)/len(s):.0f} s  |  mean GPU energy {sum(e)/len(e):.2f} Wh per grading" if e else "")


def main(keys):
    if keys == ["summary"]:
        return summary()
    pairs = json.load(open(HERE / "bias_pairs.json"))
    cases = {c["id"]: c for c in load_cases()["cases"]}
    judge = get_provider(role="judge")
    res = json.load(open(OUT)) if OUT.exists() else {}
    for key in keys:
        cid, version = key.split(":")
        answer = pairs[cid][version]
        print(f"{B}{cid} ({version}){X}  {D}{len(answer.split())} words, judge {provider_label(judge)}{X}", flush=True)
        out, idle, avg = grade(cases[cid], judge, answer)
        r = out["result"]
        secs = out["latency_seconds"]
        energy = avg * secs / 3600 if avg else None
        save_run([out], course="bias_check", version=key, provider=provider_label(judge), student=f"bias:{version}", source="bias")
        res[key] = {"score": r.get("score"), "verdict": r.get("verdict"), "status": out["status"],
                    "missing": r.get("missing_points") or r.get("missing_controls") or r.get("missing_reasoning") or [],
                    "errors": r.get("technical_errors") or r.get("design_flaws") or r.get("risk_gaps") or [],
                    "seconds": round(secs, 1), "gpu_idle_w": idle, "gpu_avg_w": round(avg, 1) if avg else None,
                    "energy_wh": round(energy, 3) if energy else None}
        json.dump(res, open(OUT, "w"), indent=2)
        col = G if r.get("verdict") == "pass" else R
        print(f"  {col}{r.get('score')}/10 {str(r.get('verdict')).upper()}{X}  {secs:.0f} s  |  GPU {avg:.0f} W avg "
              f"(idle {idle:.0f} W)  |  {energy:.2f} Wh" if avg else f"  {r.get('score')} {r.get('verdict')}")
        for item in res[key]["missing"]:
            print(f"   - missing: {item}")
        for item in res[key]["errors"]:
            print(f"   - finding: {item[:140]}")


if __name__ == "__main__":
    main(sys.argv[1:])
