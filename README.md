# J_AI

> Structured AI evaluation engine: templates in, validated JSON verdicts out. Local-first via Ollama.

## Purpose
Evaluate technical answers consistently instead of generating conversational responses that grade differently every time.

## Problem Solved
LLM evaluations are inconsistent: same answer, different verdicts. J_AI moves the evaluation criteria *outside* the model (Decision 0003): versioned templates define objectives, scoring criteria, and required output; the model interprets answers only within those boundaries.

## Technologies Used
Python · Ollama 0.34 (local LLM: qwen3.8:27b default, gpt-oss:20b fast alternative, qwen2.5:14b, llama3) · schema-enforced structured output · native tool calling (agent) · thinking control · versioned prompt templates

## My Role
Sole designer and developer. Architecture documented in my Engineering Journal (Decisions 0003–0009, 0040–0044, 0072).

## Architecture
```
Scenario + Student Answer + Template (+ the case's marking scheme)
        ↓  prompt assembly (input guard: too-short answers never reach the model)
     Local LLM (Ollama; provider-agnostic via factory; judge/student roles; thinking control)
        ↓  schema-enforced verdict (Ollama format) with JSON validation + rescue as fallback
 status-tagged result (graded / guard_rejected / provider_error)
        ↓
 run file → scoreboard (scorers) → markdown report (report)

Student agent (jai/agent): model drafts → submit_answer tool → the pipeline above → verdict → revise → repeat
```

## Usage
Full guide with install steps, adding your own cases and marking schemes, provider switching, and troubleshooting: **[docs/USAGE.md](docs/USAGE.md)**.
```bash
cd code && pip install -r requirements.txt && cp .env.example .env
python -m unittest discover -s tests   # 22 tests, fake provider, no model needed

# grade one answer against a stored case (exit 0 pass, 1 fail, 2 error)
python cli.py evaluate --case REQ_001 --answer myanswer.txt

# grade all cases from an answers file, then aggregate and render
JAI_MODE=eval JAI_EVAL_ANSWERS=answers.json python main.py
python -m jai.eval.scorers          # scoreboard for the newest run
python -m jai.eval.report           # markdown report into outputs/
```

## Real example
The same three answers graded on 2026-09-10 by the adopted judge (qwen3.8:27b) are in [docs/examples/report_jaber_answers_qwen38.md](docs/examples/report_jaber_answers_qwen38.md): scores 4, 1, 1, every missing point named, every technical error quoted ("build a server ... that can connect all 35 PCs": a server is not an access device). Below, the first run from 2026-09-03 (llama3 on GPU) for comparison. The student answered three of five cases; the examiner graded consistently and the guard refused the blanks:

```json
{
  "cases_total": 5,
  "cases_graded": 3,
  "cases_guard_rejected": 2,
  "cases_provider_error": 0,
  "average_score": 2.4,
  "pass_rate": 0.0,
  "avg_model_latency_seconds": 4.12
}
```

A graded verdict, verbatim (the answer described operations and staffing; the rubric wanted the engineering framework):

```json
{
  "case_id": "REQ_001",
  "status": "graded",
  "result": {
    "score": 4,
    "verdict": "fail",
    "missing_points": [
      "clearly separate business goals and technical goals",
      "identify constraints"
    ]
  }
}
```

And the guard doing its job on a blank answer, model never called:

```json
{
  "case_id": "PROT_001",
  "status": "guard_rejected",
  "latency_seconds": 0.0,
  "result": { "score": 0, "verdict": "fail",
              "reason": "answer too short to grade (under 20 characters)" }
}
```

## Student agent (the examiner as a tool)
Added 2026-09-10. The first agent in J_AI turns the pipeline around: the model sits the exam, and the examiner is the only tool it may call. It drafts an answer, submits it through `submit_answer`, reads the verdict, revises on the cited gaps, and repeats until the verdict is pass or five submissions are spent. The agent never sees a case's `expected` block: it learns from feedback, not from the answer key.

```bash
python -m jai.agent.student --case REQ_001            # exit 0 pass, 1 not passed, 2 error
```

Guardrails: a 12-step cap, a 5-submission cap, two nudges at most when the model answers without submitting (it tried in 5 of 8 test runs), refusal of any tool that does not exist, and the rule that only a graded submission can be the final answer (after passing, the model rewrote its answer in the closing text; that version had never been examined). Every run writes a JSON record to `runs/` and a readable transcript to `outputs/`. Every stop reason and guardrail is covered by `tests/test_student_agent.py` with a scripted fake provider (`python -m unittest tests.test_student_agent -v`).

What it found on day one, with qwen2.5:14b as both student and judge (transcripts in [docs/examples](docs/examples/)):

| case | score | judge verdict | required points listed missing |
|---|---|---|---|
| LOG_001 | 6 | pass | 4 of 5 (min_points 5) |
| REQ_001 | 7 | pass | 2 of 5 (min_points 5) |
| REQ_002 | 7 | pass | 2 of 5 (min_points 5) |
| SEC_001 | 7 | pass | 2 of 5 (min_points 5) |

The judge's pass/fail is not tied to its own marking scheme. With `--strict`, the revise loop ran for real: REQ_001 went four submissions (6, 8, 8, 8) and still failed, because the judge kept marking "separate business and technical goals" missing on an answer that opened with explicit *Business Goals* and *Technical Requirements* headings. A false negative, and the student looped on it until the guard stopped the run. The strict check was the agent's own flag at first. Since v1.0 it lives in the runner and applies to every grading path (see Key Decisions).

## Model bake-off and the architecture change (2026-09-10)
The agent's findings above raised the question of whether the judge model, not the prompt, was the limit. Three things changed in one pass:

- **Roles.** The judge and the student are configured separately (`JAI_JUDGE_MODEL`, `JAI_STUDENT_MODEL`, and matching `_THINK` settings), so any model can grade any other.
- **Schema-enforced verdicts.** The verdict contract is now a JSON schema in the runner, passed to Ollama's `format` field, so the shape is guaranteed at the source. Prompt-only JSON with retry and rescue remains as the fallback (`JAI_STRUCTURED=0`).
- **Thinking control.** `think` is passed through to models that support it (`true`/`false` for the qwen3 family, `low`/`medium`/`high` for gpt-oss).

The bake-off ran the student agent on all five cases in strict mode, each model as both student and judge. Ollama was upgraded from 0.17.0 to 0.34.0 mid-way so the Qwen 3.x family could take part:

| model | strict passes | submissions | nudges | judge "pass" with too many points missing | wall time |
|---|---|---|---|---|---|
| qwen2.5:14b | 0 of 5 | 17 | 9 | 16 of 17 | 375s |
| gpt-oss:20b, think=low | 5 of 5 | 5 | 0 | 0 of 5 | 198s |
| qwen3.8:27b, think=low | 5 of 5 | 6 | 0 | 0 of 5 | 1027s |

Clean passes from a model grading itself were not taken on trust, so every judge graded the other models' final answers plus deliberately weak and partial control answers. qwen2.5 passed everything while listing missing points each time. gpt-oss's verdicts followed the marking scheme and it failed the controls, but it gave 10/10 to every strong-looking answer, including one with a counting error. qwen3.8 was the only judge that failed a strong model's first draft (LOG_001, 3/10 for no hierarchy, no addressing plan, no redundancy, then 8/10 after revision), and on gpt-oss's REQ_002 answer it caught four switches times three labs against a six-lab scenario, spine-leaf used for a three-tier design, and ports confused with uplinks, each finding ending with the quote that proves it. Its weak controls scored 0 to 1, partial controls 1 to 4, all fails.

**qwen3.8:27b at low thinking effort is the default for both roles.** Costs, stated plainly: at 17GB it spills past a 16GB card into RAM, so a grading takes 50 to 140 seconds and a full agent run three to six minutes; the request timeout is 600s and the structured-output budget 4096 tokens (at 1024 it truncated 3 of 17 verdicts). gpt-oss:20b stays on disk as the fast judge, five times quicker, for batch runs where verdict consistency matters more than fine findings. Transcripts in [docs/examples](docs/examples/).

## Key Decisions
- Evaluation logic lives in templates, not prompts scattered per use (0003).
- Templates are versioned, never edited in place, for reproducibility (0004).
- JSON is the only output contract: machine-readable and validatable (0005).
- Local-first via Ollama: privacy, zero API cost, infrastructure understanding (0006).
- Never let the judge see an empty paper: answers under 20 characters are refused before the model runs (2026-09-03).
- The verdict shape is enforced by the runtime through a JSON schema, not requested in the prompt and repaired afterwards (2026-09-10).
- No model grades itself unchecked: judges are chosen by cross-grading and control answers (2026-09-10).
- The pass line is a rule, so it is applied as code: a judge "pass" with more required points missing than `min_points` allows becomes a fail, and the judge's own verdict is kept beside it (2026-10-11).

## Challenges
- **Missing dependency on install.** The Ollama installer failed on a missing `zstd`. Diagnosed from the error output and fixed with `apt install zstd` before reinstalling (Phase 3).
- **Lost administrative access.** Ubuntu user credentials had to be reset inside WSL before development could continue (Phase 2).
- **Inconsistent evaluations.** The core problem: identical answers received different verdicts run to run. Solved architecturally, not with better prompts: criteria moved out of the model into versioned templates, temperature pinned to 0, output constrained to JSON.
- **GPT provider blocked by quota.** The OpenAI key validated but requests failed on insufficient quota. The architecture stayed provider-ready and development continued fully local and cost-free (Phase 8).
- **Environment precedence conflict.** Shell-exported variables silently overrode `.env` values. Resolved with a single configuration entry point through python-dotenv (Phase 8).
- **A judge that passed blank answers.** The first full run scored two empty answers 8/10 and 6/10. The input guard now refuses them before the model is called.
- **A judge whose pass ignored its own scheme.** Found by the student agent, measured in the bake-off, and closed by the marking-scheme check in the runner.
- **Works on my machine.** A clean-clone test before v1.0 showed the install guide could not run the tool, because the optional OpenAI package was imported at startup. Fixed with a lazy import and a requirements file, and now covered by a test.

## What I Learned
J_AI changed how I see AI: before, a technology that generates responses; after, **one module inside a larger software architecture**. The model was never the problem, the architecture was. Reliable AI systems need validation, structured outputs, versioning, documentation, and testing around the model, and those surrounding systems often contribute more to quality than the model itself. Prompt engineering matured from "writing better instructions" into **software specification**: a formal contract between the system and the model. And a bigger model is not automatically a better judge. It has to be calibrated on answers whose grade you already know.

## Timeline
Development began in **2025** (Phases 1 to 8: WSL environment, Ollama, provider architecture, eval templates; see `docs/Project Journal - J_AI.docx` with build screenshots). The project journal was started in February 2026 and the code was imported to git on 2026-09-02, which is why file and commit dates are later than the work. Minimum Useful Version on 2026-09-05, student agent and model bake-off on 2026-09-10, v1.0 hardening on 2026-10-11. The journal covers all of it in 17 phases.

## Current Status
**v1.0 candidate** (2026-10-11). Everything in the [SPEC.md](SPEC.md) v1.0 checklist is done except the practice loop, where I re-answer two cases framework-first and regrade. The tag follows that.

What runs today, all local in WSL2: input guard, CLI, batch evaluation, scoreboard, markdown reports, schema-enforced verdicts with a marking-scheme check, judge and student roles, thinking control, and the student agent. qwen3.8:27b is the default judge. 22 unit tests run without a model.

## Next Improvements (v2)
Evaluation history across runs · more subjects and templates · document analysis (see the journal's Future Roadmap).

## Known Limitations
- **Speed.** qwen3.8:27b is larger than a 16GB card, so one grading takes 50 to 140 seconds. gpt-oss:20b is five times faster with less detailed findings.
- **Missing-point counting is literal.** The marking-scheme check counts everything the judge lists as missing, including the template's own checklist questions, so it errs on the strict side.
- **Five cases, one course.** The case set is ITE 402 network design only; the engine is general, the content is not yet.
- **No history or dashboard.** Each run is a file; comparing runs over time is manual.
- **Scores run generous on strong answers.** Verdicts are the trustworthy signal; a score of 8 against 9 means little.
