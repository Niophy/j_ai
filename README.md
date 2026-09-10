# J_AI

> Structured AI evaluation engine — templates in, validated JSON verdicts out. Local-first via Ollama.

<!-- Standard portfolio format (Journal, Decision 0078). Fill sections as the MUV gets built; keep each answer short. -->

## Purpose
Evaluate technical answers consistently instead of generating conversational responses that grade differently every time.

## Problem Solved
LLM evaluations are inconsistent: same answer, different verdicts. J_AI moves the evaluation criteria *outside* the model (Decision 0003): versioned templates define objectives, scoring criteria, and required output; the model interprets answers only within those boundaries.

## Technologies Used
Python · Ollama (local LLM: gpt-oss:20b default, qwen2.5:14b, llama3) · schema-enforced structured output · native tool calling (agent) · versioned prompt templates

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
# grade one answer against a stored case (exit 0 pass, 1 fail, 2 error)
python cli.py evaluate --case REQ_001 --answer myanswer.txt

# grade all cases from an answers file, then aggregate and render
JAI_MODE=eval JAI_EVAL_ANSWERS=answers.json python main.py
python -m jai.eval.scorers          # scoreboard for the newest run
python -m jai.eval.report           # markdown report into outputs/
```

## Real example
From an actual run (ITE 402 network-design cases, llama3 on GPU). The student answered three of five cases; the examiner graded consistently and the guard refused the blanks:

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
python -m jai.agent.student --case LOG_001 --strict   # apply the case's min_points count to the verdict
```

Guardrails: a 12-step cap, a 5-submission cap, two nudges at most when the model answers without submitting (it tried in 5 of 8 test runs), refusal of any tool that does not exist, and the rule that only a graded submission can be the final answer (after passing, the model rewrote its answer in the closing text; that version had never been examined). Every run writes a JSON record to `runs/` and a readable transcript to `outputs/`.

What it found on day one, with qwen2.5:14b as both student and judge (transcripts in [docs/examples](docs/examples/)):

| case | score | judge verdict | required points listed missing |
|---|---|---|---|
| LOG_001 | 6 | pass | 4 of 5 (min_points 5) |
| REQ_001 | 7 | pass | 2 of 5 (min_points 5) |
| REQ_002 | 7 | pass | 2 of 5 (min_points 5) |
| SEC_001 | 7 | pass | 2 of 5 (min_points 5) |

The judge's pass/fail is not tied to its own marking scheme. With `--strict`, the revise loop ran for real: REQ_001 went four submissions (6, 8, 8, 8) and still failed, because the judge kept marking "separate business and technical goals" missing on an answer that opened with explicit *Business Goals* and *Technical Requirements* headings. A false negative, and the student looped on it until the guard stopped the run. Open decision: move the min_points post-check into the runner, or keep the judge's verdict and report the count separately.

## Model bake-off and the architecture change (2026-09-10)
The agent's findings above raised the question of whether the judge model, not the prompt, was the limit. Three things changed in one pass:

- **Roles.** The judge and the student are configured separately (`JAI_JUDGE_MODEL`, `JAI_STUDENT_MODEL`, and matching `_THINK` settings), so any model can grade any other.
- **Schema-enforced verdicts.** The verdict contract is now a JSON schema in the runner, passed to Ollama's `format` field, so the shape is guaranteed at the source. Prompt-only JSON with retry and rescue remains as the fallback (`JAI_STRUCTURED=0`).
- **Thinking control.** `think` is passed through to models that support it (`true`/`false` for the qwen3 family, `low`/`medium`/`high` for gpt-oss).

The bake-off ran the student agent on all five cases in strict mode, each model as both student and judge. The Qwen 3.x family (the strongest open tool-callers) refused to pull on Ollama 0.17.0, so the contest on this machine was qwen2.5:14b against gpt-oss:20b:

| model | strict passes | submissions | nudges | judge "pass" with too many points missing | wall time |
|---|---|---|---|---|---|
| qwen2.5:14b | 0 of 5 | 17 | 9 | 16 of 17 | 375s |
| gpt-oss:20b, think=low | 5 of 5 | 5 | 0 | 0 of 5 | 198s |

Five clean tens from a model grading itself were not taken on trust. Cross-grading: gpt-oss graded qwen's final answers with verdicts consistent with the marking scheme in 5 of 5 (one honest fail at 3/10), gave three deliberately weak control answers 0/10 with every required point listed missing, while qwen graded gpt-oss's answers pass 5 of 5 with a required point listed missing every time. gpt-oss:20b is now the default for both roles. Known calibration item: its scores run generous (many 10s); its verdicts are the trustworthy part. Transcripts in [docs/examples](docs/examples/).

## Key Decisions
- Evaluation logic lives in templates, not prompts scattered per use (0003)
- Templates are versioned, never edited in place — reproducibility (0004)
- JSON is the only output contract — machine-readable, validatable (0005)
- Local-first via Ollama — privacy, zero API cost, infrastructure understanding (0006)

## Challenges
- **Missing dependency on install** — the Ollama installer failed on a missing `zstd`; diagnosed from the error output and fixed with `apt install zstd` before reinstalling (Phase 3).
- **Lost administrative access** — Ubuntu user credentials had to be reset inside WSL before development could continue (Phase 2).
- **Inconsistent evaluations** — the core problem: identical answers received different verdicts run to run. Solved architecturally, not with better prompts: criteria moved out of the model into versioned templates, temperature pinned to 0, output constrained to JSON.
- **GPT provider blocked by quota** — OpenAI key validated but requests failed on insufficient quota; kept the architecture provider-ready and continued fully local and cost-free (Phase 8).
- **Environment precedence conflict** — shell-exported variables silently overrode `.env` values; resolved by establishing a single configuration entry point through python-dotenv (Phase 8).

## What I Learned
J_AI changed how I see AI: before, a technology that generates responses; after, **one module inside a larger software architecture**. The model was never the problem — the architecture was. Reliable AI systems need validation, structured outputs, versioning, documentation, and testing around the model, and those surrounding systems often contribute more to quality than the model itself. Prompt engineering matured from "writing better instructions" into **software specification** — a formal contract between the system and the model.

## Timeline
Development began **February 2026** (Phases 1–8: WSL environment, Ollama, provider architecture, eval templates — see `docs/Project Journal - J_AI.docx` with build screenshots). Imported to git on 2026-09-02, which is why commit dates are later than the work.

## Current Status
**Minimum Useful Version complete** (2026-09-05): input guard, CLI, explicit error-state modeling, scoreboard, markdown reports, and a structured code review with 10 of 10 findings fixed. Rubric grading and judge calibration landed 2026-09-05. Student agent landed 2026-09-10 and exposed that the qwen2.5 judge's verdict ignores min_points; the same-day bake-off replaced it with gpt-oss:20b (schema-enforced verdicts, thinking control, judge/student roles). Next: decide whether the min_points post-check also belongs in the runner, and calibrate gpt-oss's generous scores.

Working local runtime in WSL2 (`/home/j/J_AI`): Ollama + llama3 inference, provider-agnostic architecture (base provider → factory → env-selected), `.env` config layer, and an eval module with versioned templates, runner, scorers, and test cases. Build history in `docs/Project Journal - J_AI.docx` (Phases 1–8). MUV gap: CLI evaluate command, JSON validation with retry, report writer, README examples, GitHub publish — see [SPEC.md](SPEC.md).

## Next Improvements
Multi-subject templates · evaluation history · model comparison · document analysis (see journal's Future Roadmap).

## Known Limitations
From the project journal — these define the next stage, not failures:
- Not yet packaged as a clean CLI tool (the MUV closes this)
- Validation is minimal; no formal testing dataset yet
- No persistent evaluation history or dashboard
- No multi-template management interface
- No automatic comparison between model evaluations
