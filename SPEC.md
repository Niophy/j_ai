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
- Week 2 (2026-09-10): **Student agent.** First real agent in J_AI: the model sits the exam and the examiner is its only tool (`python -m jai.agent.student --case REQ_001`). Loop: draft, submit_answer, read verdict, revise, until pass or 5 submissions; guardrails are a 12-step cap, a 2-nudge cap for answering without submitting, refusal of unknown tools, and the rule that only a graded submission counts as the final answer. Never sees the case's expected block. Decision: the agent exists to probe the judge from the student's side. Found on day one: qwen passes every first draft while listing required points as missing (LOG_001: 4 of 5 missing, verdict pass). The verdict field ignores min_points. `--strict` enforces the count agent-side until the post-check moves into the runner. Also found a judge false negative (explicit "Business Goals" heading marked as not separating goals). Recall move: "the judge's pass is not the rubric's pass."
- Week 2, part 2 (2026-09-10): **Model bake-off and architecture change.** Three moves: judge and student are separate roles (`JAI_JUDGE_MODEL` / `JAI_STUDENT_MODEL`, `_THINK`), verdicts are schema-enforced at the source (VERDICT_SCHEMA in the runner passed to Ollama `format`, old retry/rescue path kept as fallback), and `think` passes through. Contest: qwen2.5:14b vs gpt-oss:20b (Qwen 3.x refused to pull on Ollama 0.17.0). Same five cases, strict, model as both sides: qwen 0/5 with 16 of 17 verdicts inconsistent with its scheme; gpt-oss 5/5, one submission each, zero nudges. Cross-graded to make sure: gpt-oss's verdicts followed the scheme on qwen's answers and it gave deliberately weak answers 0. Then Jaber upgraded Ollama (0.34.0) and qwen3.8:27b joined: 5/5, and the only judge that failed a strong first draft (LOG_001 3 then 8) and caught arithmetic and terminology errors in gpt-oss's answers with quotes. Truncated 3 of 17 verdicts at 1024 tokens (thinking eats the budget): structured budget raised to 4096, timeout to 600s. Decision: qwen3.8:27b think=low is the default for both roles; gpt-oss:20b stays as the fast judge. Recall move: "never trust a model grading itself; cross-grade."
- Week 3:
- Week 4:
- Week 5:
- Week 6:
