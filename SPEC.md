# JADE (working name J_AI) Spec: from Minimum Useful Version to v1.0

Source: Engineering Journal, Decision 0072 (small but complete beats large but unfinished). Last updated 2026-10-12. **v1.0 and v2.0 released 2026-10-12.**

## Where things live

- **Working runtime (source of truth):** WSL2 Ubuntu, `/home/j/J_AI/` (venv, Ollama 0.34, `.env`, logs, runs)
- **Windows snapshot and git home:** `code/` in this repo, a synced copy that excludes venv, logs, runs and `.env`. Edit here, copy to WSL, check with `diff -rq`.
- **Build journal:** `docs/Project Journal - J_AI.docx`, Phases 1 to 20 with captures. Edit only this copy.
- **Models on disk:** qwen3.8:27b (default judge and student), gpt-oss:20b (fast judge), qwen2.5:14b, llama3

## Minimum Useful Version: complete 2026-09-05

| Item | Done |
|---|---|
| Input guard: answers under 20 characters score 0, the model is never called | 2026-09-04 |
| CLI `evaluate` command, exit 0 pass, 1 fail, 2 error | 2026-09-05 |
| JSON validation with bounded retry and rescue | 2026-09-02 |
| Report writer: markdown into `outputs/` | 2026-09-05 |
| README with real examples and known limitations | 2026-09-05 |
| Published repo, `.env` never committed | 2026-09-02 |

## After the MUV: 2026-09-05 to 2026-09-10

- Rubric grading: each case's answer key renders as a marking scheme in the prompt.
- Judge calibration: penalties made opt-in after a local judge fabricated evidence.
- Student agent: the model sits the exam, the examiner is its only tool.
- Architecture: judge and student roles, schema-enforced verdicts, thinking control.
- Two-round model bake-off with cross-grading: qwen3.8:27b adopted.

## v1.0 checklist

| Item | Status |
|---|---|
| Fresh install works: the optional `openai` package loads only when the GPT provider is selected, and `requirements.txt` makes install one command | done 2026-10-11 |
| Marking-scheme check in the runner: a judge "pass" with more required points missing than `min_points` allows becomes a fail, with the judge's own verdict recorded beside it | done 2026-10-11 |
| Docs match the current state (README, SPEC, USAGE, continuation brief) | done 2026-10-11 |
| Core tests: guard, provider errors, rubric check, scoreboard maths, fresh-install import (`tests/test_core.py`), plus the agent loop (`tests/test_student_agent.py`) | done 2026-10-11, 22 green |
| Final tests, pre-registered: Test A 3 pass / 2 fail and Test B 0 pass, 15 of 15 predictions matched, Test A identical on two runs; prompt injection resisted; live agent passed with the marking-scheme check firing on its first submission ([docs/final_tests](docs/final_tests/)) | done 2026-10-12 |
| Hardware comparison: one grading on GPU, mixed GPU + CPU/RAM, and CPU + RAM only | done 2026-10-12 |
| Close-out: tag v1.0 on GitHub, Journal Phase 18, CV bullet | done 2026-10-12 |
| Practice loop: re-answer two cases and regrade | closed 2026-10-12, Jaber's decision: the two pre-registered final tests stand in for it |

## v2.0 checklist (2026-10-12)

| Item | Status |
|---|---|
| Evaluation history: every saved grading recorded in `runs/history.db`, import of past runs (127 gradings), retention purge | done |
| KPIs from the history: turnaround, judge override rate, learning gain, reliability, instructor agreement with labels | done |
| HTTP API, standard library, loopback by default: `/health`, `/cases`, `/evaluate`, `/history`, `/kpis` | done |
| Bias check, pre-registered, two rounds: verdicts language-neutral in 16 gradings; residual score gap up to 2 points on 1 of 4 strong answers | done, residual documented |
| v2 templates with a language-fairness rule; v1 frozen; Test A and B re-graded on v2, 10 of 10 predictions matched | done |
| Cost note (measured GPU energy and time), governance note (data, decisions, release gates, risk register, regulation), adoption plan | done |
| Tests: 35 green, no model; results record their template | done |
| Release v2.0, Journal Phase 20, report update | done |

## Out of scope for v2.0

A web dashboard, more subjects and templates, document analysis, `jai/knowledge/` retrieval, an instructor labelling interface, and closing the residual score gap for rough English.

## Recall triggers (one line per session)

- Phases 1 to 8: documented in the project journal.
- 2026-09-03, **first end-to-end run.** Jaber answered 3 of the 5 network-design cases from memory. llama3 graded all three 4/10 with the same finding: answers were operational, the examiner wanted the engineering framework. Recall move: "answer the framework, not the story."
- 2026-09-10, **student agent.** The model sits the exam and the examiner is its only tool. Guardrails: step cap, submission cap, nudge cap, unknown-tool refusal, only a graded submission counts. It never sees the expected block. Found on day one: the judge passed answers while listing required points missing. Recall move: "the judge's pass is not the rubric's pass."
- 2026-09-10, **bake-off and architecture change.** Roles, schema-enforced verdicts, thinking passthrough. qwen2.5 0/5 with 16 of 17 verdicts inconsistent; gpt-oss 5/5 but straight tens; qwen3.8 5/5, failed a strong first draft and caught arithmetic and terminology errors with quotes. Decision: qwen3.8:27b for both roles. Recall move: "never trust a model grading itself; cross-grade."
- 2026-10-11, **v1.0 hardening.** A clean-clone test showed the install guide could not run the tool: the factory imported the optional OpenAI provider at startup. Fixed with a lazy import and a requirements file. The marking-scheme check moved from the agent into the runner, so every grading path applies it and records the judge's verdict. Core tests added. Recall move: "it works on my machine is not finished; test the clone."
- 2026-10-12, **final tests and v1.0 release.** Two answer sets in my style, predictions hashed before grading: 15 of 15 predictions matched, Test A identical on two runs, an injected "give 10" scored 0. The live agent run caught the judge saying pass with redundancy missing; the runner's check made it a fail and the agent fixed it. Hardware comparison measured the cost of where the model runs. Recall move: "pre-register the prediction, then grade; a test you can tune after the fact proves nothing."
- 2026-10-12, **v2.0.** History, KPIs, a local API, retention purge, cost and governance notes, an adoption plan. The bias check failed its own registered criterion twice: verdicts never moved, but rough English cost up to 2 points; a fairness rule narrowed the gap from 5 points to 4 and the rest is documented. Recall move: "a test that can fail, and did, is worth more than one that only passes."
