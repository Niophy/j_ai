# J_AI

> Structured AI evaluation engine — templates in, validated JSON verdicts out. Local-first via Ollama.

<!-- Standard portfolio format (Journal, Decision 0078). Fill sections as the MUV gets built; keep each answer short. -->

## Purpose
Evaluate technical answers consistently instead of generating conversational responses that grade differently every time.

## Problem Solved
LLM evaluations are inconsistent: same answer, different verdicts. J_AI moves the evaluation criteria *outside* the model (Decision 0003): versioned templates define objectives, scoring criteria, and required output; the model interprets answers only within those boundaries.

## Technologies Used
Python · Ollama (local LLM) · JSON schema validation · versioned prompt templates

## My Role
Sole designer and developer. Architecture documented in my Engineering Journal (Decisions 0003–0009, 0040–0044, 0072).

## Architecture
```
Scenario + Student Answer + Template
        ↓  prompt assembly
     Local LLM (Ollama)
        ↓  JSON validation (retry on invalid)
 JSON evaluation + timestamped markdown report
```

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
