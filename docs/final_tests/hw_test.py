"""J_AI hardware comparison: one case graded on GPU, mixed GPU+CPU/RAM, and CPU+RAM only.

Harness only: J_AI's code is not changed. The harness sets Ollama's num_gpu option
per run and records Ollama's own timing figures from each response.
usage: PYTHONPATH=/home/j/J_AI python hw_test.py
"""
import json
import subprocess
import time

from dotenv import load_dotenv
load_dotenv("/home/j/J_AI/.env")

from jai.eval.runner import load_cases, run_single_case
from src.providers.ollama_provider import OllamaProvider

B, G, R, Y, C, D, X = "\033[1m", "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[2m", "\033[0m"
CASE_ID = "LOG_001"
case = next(c for c in load_cases()["cases"] if c["id"] == CASE_ID)
answer = json.load(open("runs/final_tests/answers_test_a.json"))[CASE_ID]

LEGS = [  # (label, model, think, num_gpu)  num_gpu None = Ollama decides (as many layers as fit)
    ("Mixed GPU + CPU/RAM", "qwen3.8:27b", "low", None),
    ("CPU + RAM only",      "qwen3.8:27b", "low", 0),
    ("GPU only",            "gpt-oss:20b", "low", None),
    ("CPU + RAM only (control)", "gpt-oss:20b", "low", 0),
]


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def snapshot():
    ps = sh("ollama ps").splitlines()
    proc = ps[1].split("  ") if len(ps) > 1 else []
    split = next((p.strip() for p in proc if "GPU" in p or "CPU" in p), "n/a")
    vram = sh("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits")
    ram = sh("free -m | awk '/Mem:/{print $3}'")
    return split, int(vram or 0), int(ram or 0)


def make_provider(model, think, num_gpu):
    p = OllamaProvider(model=model, think=think)
    p.timeout_seconds = 3600
    base_options, base_post = p._options, p._post
    p.last = {}

    def options(o):
        merged = base_options(o)
        if num_gpu is not None:
            merged["num_gpu"] = num_gpu
        return merged

    def post(path, payload):
        data = base_post(path, payload)
        p.last = data
        return data

    p._options, p._post = options, post
    return p


print(f"\n{B}{C}{'=' * 78}\n J_AI hardware comparison  |  case {CASE_ID}, same answer every run\n"
      f" CPU: {sh('lscpu | sed -n \"s/Model name: *//p\"')}  |  GPU: {sh('nvidia-smi --query-gpu=name,memory.total --format=csv,noheader')}\n"
      f" WSL RAM: {sh('free -g | awk \"/Mem:/{print $2}\"')} GB\n{'=' * 78}{X}")

rows = []
for label, model, think, num_gpu in LEGS:
    print(f"\n{B}{label}{X}  {D}model {model}, think={think}, num_gpu={'auto' if num_gpu is None else num_gpu}{X}")
    for m in ("qwen3.8:27b", "gpt-oss:20b"):
        sh(f"ollama stop {m}")
    time.sleep(3)
    p = make_provider(model, think, num_gpu)
    print(f"{Y}loading model...{X}", flush=True)
    t = time.time()
    p.chat([{"role": "user", "content": "hi"}], options={"num_predict": 1})
    load_s = time.time() - t
    split, vram, ram = snapshot()
    print(f"   loaded in {load_s:.0f}s  |  processor: {B}{split}{X}  |  VRAM used {vram} MiB  |  WSL RAM used {ram} MiB")
    print(f"{Y}grading...{X}", flush=True)
    out = run_single_case(case, p, answer)
    d = p.last or {}
    ev, evd = d.get("eval_count", 0), d.get("eval_duration", 0) / 1e9
    pe, ped = d.get("prompt_eval_count", 0), d.get("prompt_eval_duration", 0) / 1e9
    tps = ev / evd if evd else 0
    res = out["result"]
    col = G if str(res.get("verdict")) == "pass" else R
    print(f"{B}{col}-> {res.get('score')}/10 {str(res.get('verdict')).upper()}{X}  ({out['status']})  "
          f"grading {out['latency_seconds']:.0f}s  |  generated {ev} tokens at {tps:.1f} tok/s  |  "
          f"read prompt {pe} tokens in {ped:.1f}s")
    rows.append({"setup": label, "model": model, "num_gpu": num_gpu, "processor": split,
                 "vram_mib": vram, "wsl_ram_mib": ram, "load_s": round(load_s, 1),
                 "grading_s": round(out["latency_seconds"], 1), "eval_tokens": ev,
                 "tokens_per_s": round(tps, 1), "prompt_tokens": pe, "prompt_s": round(ped, 1),
                 "status": out["status"], "score": res.get("score"), "verdict": res.get("verdict")})

json.dump(rows, open("runs/final_tests/hardware_test.json", "w"), indent=2)
print(f"\n{B}{C}{'-' * 78}\n RESULTS{X}")
print(f"{B} {'setup':26} {'processor':17} {'load':>6} {'grading':>8} {'tok/s':>6}  score{X}")
for r in rows:
    print(f" {r['setup']:26} {r['processor']:17} {r['load_s']:>5.0f}s {r['grading_s']:>7.0f}s {r['tokens_per_s']:>6.1f}  {r['score']}/10 {r['verdict']}")
print(f"{D}\n saved runs/final_tests/hardware_test.json{X}\n")
