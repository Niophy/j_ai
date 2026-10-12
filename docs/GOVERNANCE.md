# JADE governance note (v2.0)

How JADE's data, decisions and changes are controlled. It describes the system as built; it is guidance for an operator, not legal advice.

## Data JADE holds

| Data | Where | Contains personal data | Retention control |
|---|---|---|---|
| Run files | `runs/run_*.json` | Yes: answers, optional student name | Delete files older than the policy |
| Evaluation history | `runs/history.db` (SQLite) | Yes: answers, answer hashes, student names | `python cli.py history --purge-before YYYY-MM-DD` |
| Reports | `outputs/*.md` | Yes: answers quoted back | Delete with the run files |
| Agent records | `runs/agent_*.json` | No student data (model-written answers) | Optional |
| Configuration | `.env` | No; may hold keys for a cloud provider | Never committed to git |

**Everything stays on the machine.** The default provider is a local model through Ollama; no answer leaves the computer. The API binds to the loopback address, and returns no answer text from its history endpoint.

**Recommended retention policy.** Keep gradings for one teaching term plus the appeal window, then purge. Set `JAI_HISTORY=0` where no history should be kept at all.

## Who decides

- **JADE's role is formative.** It gives practice feedback; it does not issue final grades.
- **The instructor owns the marking schemes** (`cases.json`) and has the final say on any verdict.
- **Every override is visible.** When the marking-scheme check turns a judge "pass" into a fail, the judge's own verdict stays in the record and the report prints the override.
- **No finding without evidence.** Every error the judge lists must quote the answer; penalty items stay opt-in after a judge was caught fabricating a quote.

## Changing the system

A change to the judge model, a template or the marking-scheme logic is released only after these gates:

1. All unit tests pass (35 at v2.0, no model needed).
2. A clean clone installs from the requirements file and passes the tests.
3. A pre-registered test: answers and predictions hashed before grading, nothing edited afterwards.
4. The bias check (same content in polished and rough English) is re-run and reported.

Templates are versioned and never edited in place. Example: the v2.0 fairness rule shipped as new `_v2` templates, v1 stayed frozen, and Test A and Test B were re-graded on v2 (10 of 10 predictions matched) before release.

## Risk register

| Risk | Status at v2.0 | Control |
|---|---|---|
| Prompt injection inside an answer | Tested: scored 0, attempt quoted as an error | Schema-enforced output, coded pass line |
| Verdict depends on the student's English | Tested in 16 gradings: never | Bias check before every release |
| Score depends on the student's English | Residual: up to 2 points on 1 of 4 strong answers | Fairness rule (v2); decisions use verdicts, not scores |
| Judge passes work with required points missing | Controlled | Marking-scheme check in code |
| Judge scores strong answers generously | Known | Verdicts and named findings are the trusted signal |
| Model change silently shifts grading | Controlled | Release gates above; run files record model and template |
| Answers exposed over the network | Controlled | Loopback-only API; widen only behind an authenticating proxy |

## Regulation

JADE processes students' written answers, which are personal data. The operator applies the personal-data law of the place it is deployed: in the United Arab Emirates, Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data; the GDPR for students in the EU; FERPA for US education records. The design keeps that exposure small: local processing, no third-party transfer, a purge command, and no answer text in the API's history.
