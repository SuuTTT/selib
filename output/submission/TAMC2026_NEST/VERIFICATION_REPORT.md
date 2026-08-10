# NEST scaled-audit verification

Status: **PASS** for seven completed, hash-sealed blocks. The interrupted
exact12 checkpoint is excluded.

## 64-vertex benchmark

- 500 graph instances, 3500 method records, and 500 manifests.
- Paired gain over the better of HCSE and BBM: 0.4239 +/- 0.0086 bits (95% t interval).
- Strict wins: 500/500.

## Exact optimum audit

| n | Instances | NEST | HCSE | label-free BBM |
|---:|---:|---:|---:|---:|
| 12 | 250 | 249 | 2 | 1 |
| 14 | 100 | 99 | 0 | 0 |
| 16 | 25 | 22 | 0 | 0 |

Across the three completed size strata, NEST hits 370/375 exact optima; its exact 95% Clopper-Pearson interval is [96.92%, 99.57%].
