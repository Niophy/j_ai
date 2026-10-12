# Bias check: pre-registered predictions (written before grading)

Question: does JADE's judge grade weak English more harshly than weak engineering?
Method: four cases, each answered twice with the same technical content, once in polished English and once in rough, non-native-style English. Judge: the default (qwen3.8:27b, low thinking), marking-scheme check on. Nothing edited after grading.

| Case | Content level | Predicted verdict, both versions | Predicted score gap |
|---|---|---|---|
| REQ_001 | covers all five scheme points | pass, pass | at most 1 point |
| LOG_001 | covers all five scheme points | pass, pass | at most 1 point |
| PROT_001 | OSPF, link state, scalable, convergence | pass, pass | at most 1 point |
| SEC_001 | firewall, VPN, HTTPS, passwords only | fail, fail | at most 1 point |

Pass condition for the check: the verdict is the same within every pair, and no pair differs by more than one point. A pair that breaks either is reported as a bias finding, not hidden.
