# JADE cost note (v2.0, measured 2026-10-12)

JADE runs on local hardware, so it has no per-call fee: the cost of a grading is GPU energy and time, both measured here on the machine that runs it.

## What one grading costs

| Measure | Value | Source |
|---|---|---|
| Grading time, quality judge (qwen3.8:27b, mixed GPU and CPU) | 79 to 88 s average per batch; 60 to 119 s range | 26 gradings: bias check rounds 1 and 2, v2 regression |
| GPU power while grading | 57 to 79 W average per grading | nvidia-smi sampled every 0.5 s during each of the 16 bias-check gradings |
| GPU idle draw | 19 to 29 W | first sample before a grading, when the GPU had settled |
| GPU energy per grading | 1.58 Wh (round 1), 1.67 Wh (round 2) | average power multiplied by grading time |
| Grading time, fast judge (gpt-oss:20b, fully on the GPU) | 1 s | hardware comparison, [final_tests](final_tests/README.md) |
| Grading time, CPU only (qwen3.8:27b) | 365 s | hardware comparison |
| Per-call API fee | none | fully offline |

The energy figure covers the GPU only. CPU, memory and the rest of the system draw extra power that this measurement does not include.

## Scaled up

| Volume | Quality judge time | GPU energy |
|---|---|---|
| 100 gradings | about 2.3 hours | about 0.16 kWh |
| 1,000 gradings | about 23 hours | about 1.6 kWh |

To turn energy into money, multiply the kWh by the local electricity tariff. The cost is dominated by time, not energy: the quality judge is larger than the 16 GB card, so it spills into system RAM and the GPU sits far below full load while it waits.

## Levers

1. **Fast judge for batches.** gpt-oss:20b grades in about 1 second; it follows the marking scheme but scores strong answers generously and gives less detailed findings. Use it for practice rounds, the quality judge for results that matter.
2. **A larger GPU.** A card that holds the whole quality judge removes the spill, the main source of the 80-second grading time.
3. **Grading is serial.** One GPU grades one answer at a time; the API queues requests rather than overloading it.
