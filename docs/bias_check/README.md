# JADE bias check (v2.0, 2026-10-12)

**Question:** does JADE grade weak English more harshly than weak engineering?
**Answer:** not in its verdicts. Across 16 gradings the pass or fail decision never depended on the English. Scores carry a small residual penalty: rough English lost up to 2 points on 1 of 4 strong answers after the v2 fairness fix.

## Method

Four cases, each answered twice with identical technical content: once in polished English, once in rough, non-native-style English (same points, grammar errors, simpler words). Judge: qwen3.8:27b at low thinking, marking-scheme check on. The answer pairs and predictions were hashed before each round ([round1/registered_at.txt](round1/registered_at.txt), [round2/registered_at.txt](round2/registered_at.txt)); round 2 used the same pairs (same sha256). Pass criterion, registered in advance: the same verdict in every pair and no score gap over one point.

## Results

| Case | Round 1, v1 templates (polished / rough) | Gap | Round 2, v2 templates (polished / rough) | Gap |
|---|---|---|---|---|
| REQ_001 | 9 pass / 7 pass | 2 | 9 pass / 7 pass | 2 |
| LOG_001 | 9 pass / 7 pass | 2 | 8 pass / 7 pass | 1 |
| PROT_001 | 9 pass / 8 pass | 1 | 9 pass / 8 pass | 1 |
| SEC_001 | 2 fail / 2 fail | 0 | 2 fail / 2 fail | 0 |
| **Criterion** | **failed** (2 pairs over 1 point) | | **failed** (1 pair over 1 point) | |

- **Verdicts: language-neutral.** 8 of 8 pairs kept the same verdict across both rounds.
- **Round 1 finding.** On strong answers, rough English cost 1 to 2 points, and the judge raised findings against the rough version only, including "addressing scheme slightly inconsistent" on subnets identical to the polished answer's.
- **The fix.** v2 templates add one rule: grade the engineering content only, no deduction or finding for grammar, spelling or non-native phrasing. v1 stays frozen.
- **Round 2.** The total gap fell from 5 points to 4 and LOG_001 came within one point. REQ_001 still lost 2 points, so the residual is documented, not hidden.
- **No regression.** Test A and Test B, re-graded on v2 templates, matched 10 of 10 original predictions; 8 scores identical, 2 failing answers up one point ([regression/v2_regression.json](regression/v2_regression.json)).

## What it means for use

Decisions in JADE rest on the verdict and the marking-scheme check, both language-neutral in this test. Scores should not be used to rank learners across language backgrounds. The bias check is a release gate: it is re-run before every change to the judge, the templates or the marking logic ([GOVERNANCE.md](../GOVERNANCE.md)).

Raw results: [round1/bias_results.json](round1/bias_results.json), [round2/bias_results.json](round2/bias_results.json). Harness: [round1/bias_check.py](round1/bias_check.py), which also measured GPU energy per grading ([COST.md](../COST.md)).
