# JADE adoption plan (v2.0)

A plan for an organization that teaches or certifies technical skills (a training provider, a technical academy, or an academic department) to pilot JADE as a formative practice examiner.

## The problem it solves

Learners cannot practise written scenario answers often enough, because every practice attempt costs an instructor's time. When feedback does arrive it is slow, and two markers can grade the same answer differently.

## What is adopted

JADE v2.0, fully offline on one GPU workstation: the examiner, the evaluation history and KPIs, and the local HTTP API for connecting a learning platform. Learners submit practice answers; JADE returns a verdict, the missing points and quoted errors within about 80 seconds.

## Pilot design (one term)

| Item | Plan |
|---|---|
| Scope | One course or module, opt-in, formative only |
| Content | The instructor writes or adapts the cases and marking schemes; JADE's five network-design scenarios are the starting set |
| Case quality check | The student agent sits each new case first: a strong answer must pass and a weak one fail before learners see it |
| Hardware | One workstation with a 16 GB GPU (measured: about 80 s and 1.6 Wh per grading) |
| Integration | The learning platform calls the local API, or learners use a shared machine |

## KPIs and targets (tracked from the evaluation history)

| KPI | Measured by | Pilot target |
|---|---|---|
| Instructor agreement | Instructor verdicts on a weekly sample, loaded as labels into `cli.py kpis --labels` | 85% or higher |
| Learning gain | Score change from first to last attempt per learner and case | Positive on average |
| Feedback turnaround | Median grading time from the history | Under 2 minutes |
| Judge alignment | Share of judge passes overridden by the marking-scheme check | Falling over the term |
| Reliability | Share of gradings ending in a provider error | Under 1% |

## Rollout

1. **Prepare (weeks 1 to 2).** Install, run the clean-install check, load the cases, run the student agent on every case.
2. **Pilot (one term).** Learners practise; the instructor labels a weekly sample.
3. **Review.** KPIs against targets, a learner and instructor survey, and a go or no-go decision.
4. **Expand.** More courses and subjects; a larger GPU if volume makes grading time the bottleneck.

## Change management

The instructor writes the marking schemes, so JADE applies the instructor's judgment rather than replacing it. Learners are told plainly what grades their practice answers and that the instructor has the final word. Overrides and findings are visible, so a disputed verdict can be traced and corrected.

## Risks

| Risk | Mitigation |
|---|---|
| Learners trust a score too much | Formative use only; verdicts and named findings are the signal |
| Non-native writers scored lower | Bias check before every release; residual score gap documented; decisions use verdicts |
| A model change shifts grading | Release gates in the governance note |
| Grading speed at volume | Fast judge for practice rounds, quality judge for checkpoints |

Supporting notes: [COST.md](COST.md), [GOVERNANCE.md](GOVERNANCE.md), [bias_check](bias_check/README.md).
