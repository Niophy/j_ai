# J_AI — Minimum Useful Version (MUV) Spec

Source: Engineering Journal, Decision 0072. Updated 2026-09-02 after locating the existing codebase.

## Where things live

- **Working runtime (source of truth):** WSL2 Ubuntu → `/home/j/J_AI/` (venv, Ollama, logs, `.env` with `JAI_PROVIDER` / `JAI_OLLAMA_MODEL` / `JAI_OLLAMA_BASE_URL`)
- **Windows snapshot (this repo):** `code/` — synced copy, excludes venv/logs/runs/.env
- **Build journal:** `docs/Project Journal - J_AI.docx` (Phases 1–8) + run screenshots in `docs/`
- Development happens in WSL; re-sync the snapshot here after meaningful changes.

## What already exists (Phases 1–8, done)

- WSL2 Ubuntu 24.04 + Ollama + llama3 local inference
- `src/providers/ollama_provider.py` — REST provider (`src/providers/gpt_provider.py` stubbed, quota-blocked)
- `src/core/base_provider.py` + `provider_factory.py` — provider-agnostic architecture, env-selected via `JAI_PROVIDER`
- `.env` configuration layer (python-dotenv)
- `jai/eval/` — `templates.py` (requirements_analysis_v1, logical_design_v1, …), `runner.py`, `scorers.py`, `cases.json`
- Interactive chat entry (`main.py`), logger

## What the MUV still needs (the gap)

```
scenario + answer + template name → CLI → valid JSON + timestamped markdown report
```

0. **Input guard (bug found 2026-09-03, Jaber's own full run):** the examiner passed two BLANK answers (8/10, 6/10) — LLM judges invent merit when given nothing. Guard in `run_single_case`: empty/trivially-short answer → score 0 / "no answer submitted", model never called.
1. **One CLI evaluate command** wiring templates + provider + runner (no interactive loop needed)
2. **JSON validation with bounded retry** — corrective re-prompt on invalid output; fail loudly
3. **Report writer** — timestamped markdown into `outputs/`
4. **README with real example evaluations + known-limitations section**
5. **Published GitHub repo** (never commit `.env`)

Out of scope for MUV: dashboard, history DB, model comparison, multi-template UI, `jai/knowledge/` RAG (empty folder = Phase 9+, capstone material).

## Build order (revised — one week per line)
1. Baseline: run the existing system end-to-end in WSL, fix the `__int__.py` → `__init__.py` typo, commit this snapshot as v0
2. CLI `evaluate` command (args: template, scenario file, answer file)
3. JSON validation + retry loop
4. Report writer + outputs folder
5. Examples, limitations, README polish
6. Publish to GitHub; exit test — explain the architecture from the README alone

## Fix pass 2026-09-02 (applied to WSL + snapshot, smoke-tested)
- `cases.json` restored from `case.json` (was empty — eval mode would have crashed); old duplicates and extra entry points (`app.py`, `main_chat_backup.py`) parked in `attic/`
- Real `__init__.py` files in all packages (typo `__int__.py` gone)
- `scorers.py` implemented: scoreboard over a run file (`python -m jai.eval.scorers`)
- Verified: JSON retry already existed in `OllamaProvider.generate_json`; all 4 templates cover all 5 cases; runner now warns loudly when retries exhaust
- Week 1 session is now: **run end-to-end with the model + first git commit** (left for Jaber deliberately)

## Recall triggers (one line per week as you go)
- Phases 1–8: documented in `docs/Project Journal - J_AI.docx` ✔
- Week 1 (2026-09-03): **First end-to-end run.** Jaber answered 3 of the 5 ITE402 cases from memory; J_AI graded via llama3 (GPU, 1–10s each), 0 invalid JSON, scoreboard worked. All three scored 4/10 with the same finding — answers were operational, examiner wanted the engineering framework (business vs technical goals, constraints, scalability). One recall move learned: "answer the framework, not the story." Run: `runs/run_1788414464.json` + `answers.json` in WSL — real example material for the MUV README.
- Week 2:
- Week 3:
- Week 4:
- Week 5:
- Week 6:
