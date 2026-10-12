# JADE bias check (v2.0 and v2.1, 2026-10-12)

**Question:** does JADE grade weak English more harshly than weak engineering?
**Answer:** not in its verdicts, and since v2.1 not in its scores for strong answers. Across 24 gradings in three rounds, the pass or fail decision never depended on the English. In v2.0 the score still carried a penalty (rough English lost up to 2 points). v2.1 computes the score from the marking scheme in code, and the three strong pairs now score the same. One residual effect remains, and it runs the other way: on the weak answer the judge misses one absent point in the rough version only.

## Method

Four cases, each answered twice with identical technical content: once in polished English, once in rough, non-native-style English (same points, grammar errors, simpler words). Judge: qwen3.8:27b at low thinking, marking-scheme check on. The answer pairs and predictions were hashed before each round ([round1](round1/registered_at.txt), [round2](round2/registered_at.txt), [round3](round3/registered_at.txt)); all rounds used the same pairs (same sha256). Pass criterion, registered in advance and never changed: the same verdict in every pair and no score gap over one point.

## Results

| Case | Round 1, v1 templates (polished / rough) | Gap | Round 2, v2 templates | Gap | Round 3, v2.1 points-based score | Gap |
|---|---|---|---|---|---|---|
| REQ_001 | 9 pass / 7 pass | 2 | 9 pass / 7 pass | 2 | 10 pass / 10 pass | 0 |
| LOG_001 | 9 pass / 7 pass | 2 | 8 pass / 7 pass | 1 | 10 pass / 10 pass | 0 |
| PROT_001 | 9 pass / 8 pass | 1 | 9 pass / 8 pass | 1 | 10 pass / 10 pass | 0 |
| SEC_001 | 2 fail / 2 fail | 0 | 2 fail / 2 fail | 0 | 2 fail / 4 fail | 2 |
| **Criterion** | **failed** (2 pairs over 1 point) | | **failed** (1 pair) | | **failed** (1 pair, in favour of rough English) | |

- **Verdicts: language-neutral.** 12 of 12 pairs kept the same verdict across three rounds.
- **Round 1 finding.** On strong answers, rough English cost 1 to 2 points with no required point missing, and the judge raised findings against the rough version only, including "addressing scheme slightly inconsistent" on subnets identical to the polished answer's.
- **Round 2 (v2.0).** A language-fairness rule in the templates cut the total gap from 5 points to 4. REQ_001 still lost 2 points with 0 points missing in both versions, which located the bias in the judge's free score.
- **Round 3 (v2.1).** The score became 10 x required points covered / required points, computed in code; the judge's own score is kept as `judge_score`. The registered prediction matched all 8 gradings: the strong pairs score 10 and 10, and the criterion fails on SEC_001 only.
- **The SEC_001 residual.** Both versions leave the public website unisolated. The judge flags that point missing in the polished version and not in the rough one, in all three rounds. The round-3 prediction called this "point counting, not the English". Because it repeats in every round, that explanation was wrong: the language still affects which points the judge detects, in 1 of 4 pairs, and here it favours the rough writer. With 5 required points, one point counted differently moves the score by 2.
- **No regression.** Test A and Test B, re-graded on v2 templates, matched 10 of 10 original predictions ([v2_regression.json](regression/v2_regression.json)). For v2.1 the same judge outputs were re-scored with the new rule, since the judge prompt is unchanged and the rule never touches the verdict: 10 of 10 still match ([v21_regression.json](regression/v21_regression.json), [rescore_v21.py](regression/rescore_v21.py)).

## What it means for use

Decisions in JADE rest on the verdict and the marking-scheme check, language-neutral in all 12 pairs. Since v2.1 a score means the share of required points covered, so a failing answer can still score up to 8 when it misses a point the scheme requires. The remaining language effect sits in point detection: a judge can overlook a missing point. Instructor review of borderline verdicts covers it. The bias check is a release gate, re-run before every change to the judge, the templates or the marking logic ([GOVERNANCE.md](../GOVERNANCE.md)).

Raw results: [round1](round1/bias_results.json), [round2](round2/bias_results.json), [round3](round3/bias_results.json). Harness: [round1/bias_check.py](round1/bias_check.py) (round 3 adds `judge_score` to each record), which also measured GPU energy per grading ([COST.md](../COST.md)).
