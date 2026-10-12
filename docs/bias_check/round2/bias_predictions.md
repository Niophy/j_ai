# Bias check round 2: pre-registered predictions (written before grading)

Round 1 (v1 templates) failed its own criterion: verdicts never changed, but rough English lost 2 points on REQ_001 and LOG_001.
Change under test: v2 templates add one language-fairness rule (grade content only; no deduction or finding for grammar, spelling or non-native phrasing). Nothing else changed: same answer pairs (same sha256 as round 1), same judge (qwen3.8:27b, low thinking), same pass criterion.

| Case | Predicted verdict, both versions | Predicted score gap |
|---|---|---|
| REQ_001 | pass, pass | at most 1 point |
| LOG_001 | pass, pass | at most 1 point |
| PROT_001 | pass, pass | at most 1 point |
| SEC_001 | fail, fail | at most 1 point |

Pass condition: the same verdict within every pair and no gap over one point. Whatever comes out is reported as it is.

Regression check, also registered now: Test A and Test B (the v1.0 final-test answer sets, unchanged) re-graded with the v2 templates should still match all 10 original predictions (Test A: pass, fail, pass, pass, fail; Test B: all fail).
