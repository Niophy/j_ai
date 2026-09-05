# J_AI Usage Guide

J_AI is a local-first AI evaluation engine: you give it exam-style questions with marking schemes, a student gives it answers, and a local language model grades them into validated JSON verdicts, scoreboards, and readable markdown reports. It was built to answer one question: can an AI evaluate technical work as consistently as an experienced examiner? Everything below runs offline on your own machine.

## Requirements

- Linux or WSL2 (developed on Ubuntu 24.04 inside WSL2)
- Python 3.10+
- [Ollama](https://ollama.com) with at least one model pulled (default: `llama3`)
- Optional: an OpenAI API key if you want the GPT provider instead of Ollama

## Install

```bash
git clone https://github.com/Niophy/j_ai.git
cd j_ai/code
python3 -m venv venv
source venv/bin/activate
pip install requests python-dotenv
ollama pull llama3
```

Copy the environment template and adjust if needed:

```bash
cp .env.example .env
```

The defaults (Ollama on localhost, llama3) work out of the box; you only edit `.env` to switch models or providers.

## Three ways to use it

### 1. Chat mode (sanity check)

```bash
python main.py
```

An interactive prompt against your local model. Type `exit` to quit. Use it once to confirm Ollama responds.

### 2. Batch evaluation (the main flow)

Write your answers to the stored cases in a JSON file, keyed by case id:

```json
{
  "REQ_001": "My answer to the clinic scenario...",
  "LOG_001": "My answer to the logical design question..."
}
```

Then run the pipeline:

```bash
JAI_MODE=eval JAI_EVAL_ANSWERS=answers.json python main.py   # grade every case
python -m jai.eval.scorers                                   # scoreboard for the newest run
python -m jai.eval.report                                    # markdown report into outputs/
```

Cases you leave out are guard-rejected (score 0, model never called), so you can answer a subset honestly.

### 3. Single evaluation from the command line

```bash
# grade one answer against a stored case
python cli.py evaluate --case REQ_001 --answer myanswer.txt

# grade anything ad hoc: your own scenario file plus an answer, using any template
python cli.py evaluate --template requirements_analysis_v1 --scenario scenario.txt --answer myanswer.txt

# pipe the answer in, save a run file for the scoreboard
echo "OSPF scales across buildings via areas..." | python cli.py evaluate --case PROT_001 --answer - --save

# discovery
python cli.py evaluate --list-cases
python cli.py evaluate --list-templates
```

Exit codes are scriptable: `0` pass, `1` fail (including guard rejections), `2` usage or runtime error (nothing was actually graded).

## Reading the output

Every result record carries exactly one `status`:

| status | Meaning |
|---|---|
| `graded` | The model produced a valid verdict |
| `guard_rejected` | The input guard refused (answer under 20 characters); the model never ran |
| `provider_error` | The model ran but returned no usable JSON |

The verdict itself contains `score` (0 to 10), `verdict` (pass or fail), and template-specific detail lists such as `missing_points`, `design_flaws`, or `incorrect_claims`. The scoreboard counts each status separately, averages scores over gradeable rows, and averages latency over model-graded rows only. The report renders all of it per case: the question, the submitted answer quoted back, and the examiner's findings.

## Make it yours

### Add a case (with its marking scheme)

Cases live in `jai/eval/cases.json`. The `expected` block is the answer key, and it drives grading: it is rendered into the prompt as a marking scheme the judge must use.

```json
{
  "id": "SEC_002",
  "type": "security_strategy",
  "prompt_template": "security_strategy_v1",
  "input": { "scenario": "Your scenario text..." },
  "expected": {
    "must_include": ["segmentation", "least privilege", "monitoring"],
    "must_avoid": ["recommending security through obscurity"],
    "min_points": 3
  }
}
```

`must_include` items become required points, `must_avoid` items become penalties, `min_points` sets the passing bar, and `must_include_any` (a list of lists) accepts any one item per group. Editing a rubric changes grading immediately.

### Add a template

Templates live in `jai/eval/templates.py`, named `<type>_vN`. Use `{scenario}` (or `{question}`) and `{student_answer}` as placeholders, and end with the JSON output instruction (`Return ONLY valid JSON: ...`) so the marking scheme injects in the right place. Version templates instead of editing them: a template that has graded real runs stays frozen, and improvements become `_v2`.

### Switch providers

Set `JAI_PROVIDER=gpt` with `OPENAI_API_KEY` and `JAI_GPT_MODEL` in `.env` to grade through OpenAI instead of Ollama. The runner's JSON validation and rescue apply to every provider.

### Tune the guard

`MIN_ANSWER_CHARS` in `jai/eval/runner.py` (default 20) is the minimum answer length that reaches the model. The marking scheme also instructs the judge to score empty or off-topic responses 0, so the guard is defense in depth, not the only defense.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| CLI exits 2 with a connection error | Ollama is not running: `ollama serve` (or check the systemd service) |
| `provider_error` results | The model returned unparseable output even after retries and rescue; try a stronger model or lower `JAI_MAX_TOKENS` pressure |
| `Unknown provider` | `JAI_PROVIDER` in `.env` is not `ollama` or `gpt` |
| Scoreboard says "No run file found" | No eval has been run yet; run batch evaluation first |
| Answers file rejected | It must be a JSON object mapping case ids to answer strings, not a list |

## Project background

The build history, including failures and the decisions behind every mechanism (the input guard, status modeling, rubric injection), is documented phase by phase with screenshots in `docs/Project Journal - J_AI.docx`.
