# Bias check round 3 (v2.1, points-based score): registered prediction

Registered before any round-3 grading. Same answer pairs as rounds 1 and 2 (same sha256), same judge (qwen3.8:27b, low thinking), v2 templates unchanged. The only change: the score is computed in code as 10 x required points covered / required points; the judge's own score is kept as judge_score.

Criterion, unchanged from rounds 1 and 2: the same verdict in every pair and no score gap over one point.

## Prediction

Derived by applying the v2.1 rule to the round-2 judge output (missing points per answer):

| Case | Polished | Rough | Gap |
|---|---|---|---|
| REQ_001 | 10 pass | 10 pass | 0 |
| LOG_001 | 10 pass | 10 pass | 0 |
| PROT_001 | 10 pass | 10 pass | 0 |
| SEC_001 | 2 fail | 4 fail | 2, in favour of the rough version |

- Verdicts: the same in 4 of 4 pairs.
- Criterion: predicted to FAIL on SEC_001 only. In round 2 the judge counted 4 of 5 points missing in the polished version and 3 of 5 in the rough one. With 5 required points, one point counted differently moves the score by 2. That gap comes from point counting, not from the English, and it favours the rough version.
- The judge is not perfectly repeatable, so a strong answer may lose one point (10 becomes 8) in either version.
