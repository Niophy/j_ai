# Pre-registered predictions (written before grading)

Judge: qwen3.8:27b think=low, marking-scheme check on (default config, unchanged).
Rule: answers and J_AI are not edited after grading. Results are reported as they come out.

## Test A: expect 3 pass, 2 fail

| Case | Prediction | Why |
|---|---|---|
| REQ_001 | pass | Names all five scheme points explicitly: business goals, technical goals, constraints, growth, security |
| REQ_002 | fail | Covers availability and wireless coverage only; no traffic types, no management, no segmentation |
| LOG_001 | pass | Hierarchy, segmentation, addressing plan, routing approach and redundancy all present |
| PROT_001 | pass | OSPF, link state, scalable through areas, convergence |
| SEC_001 | fail | Firewall, VPN, HTTPS, passwords; no segmentation, no least privilege, no monitoring, no isolation of the public website |

Confidence: high on the two fails. Medium on the three passes, because the scheme needs 5 of 5 points with no allowance, the check counts every listed missing item literally, and this judge has produced a false negative before (an explicit "Business Goals" heading marked missing).

## Test B: expect 0 pass, 5 fail

Every answer is operational (rooms, folders, projectors, antivirus) and misses most scheme points. PROT_001 picks RIP, which matches neither accepted group. Confidence: high.
