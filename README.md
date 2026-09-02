# J_AI

> Structured AI evaluation engine — templates in, validated JSON verdicts out. Local-first via Ollama.

<!-- Standard portfolio format (Journal, Decision 0078). Fill sections as the MUV gets built; keep each answer short. -->

## Purpose
Evaluate technical answers consistently — the way an experienced examiner would — instead of generating conversational responses that grade differently every time.

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
_(fill during the build)_

## What I Learned
_(fill during the build)_

## Current Status
Working local runtime in WSL2 (`/home/j/J_AI`): Ollama + llama3 inference, provider-agnostic architecture (base provider → factory → env-selected), `.env` config layer, and an eval module with versioned templates, runner, scorers, and test cases. Build history in `docs/Project Journal - J_AI.docx` (Phases 1–8). MUV gap: CLI evaluate command, JSON validation with retry, report writer, README examples, GitHub publish — see [SPEC.md](SPEC.md).

## Next Improvements
Multi-subject templates · evaluation history · model comparison · document analysis (see journal's Future Roadmap).

## Known Limitations
_(fill before publishing — honesty here is a feature)_
