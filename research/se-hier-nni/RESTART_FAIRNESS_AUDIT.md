# Fair 32-Run Restart Audit

## Protocol

- New sealed graph seeds 160--209 in five regimes (250 graphs total).
- Regime RNG streams are independent.
- Exact optima are hidden until after structural-entropy-only selection.
- NEST, HCSE, and both BBM variants receive 32 candidate calls per graph.
- HCSE cycles heights 2--5; label-free BBM cycles k=2--8; oracle BBM receives planted k=6.
- Raw candidate-level artifact: `results/nni_restart_fairness.json` (SHA-256 `8e73c814bca695336d3bfff9a0aa73c2ca280212b51f6243375b70db5f973e07`).

## Results

| Method | Valid | Exact / 250 | Mean relative gap ± 95% CI | Worst gap | Mean time |
|---|---:|---:|---:|---:|---:|
| NEST-coalescent-B32 | 250/250 | 249/250 (99.6%) | 0.000319585% ± 0.000629% | 0.0798962% | 0.171108 s |
| HCSE-B32 | 250/250 | 2/250 (0.8%) | 10.9022% ± 0.971% | 41.1383% | 0.0237928 s |
| BBM-oracle-B32 | 248/250 | 1/250 (0.4%) | 15.0538% ± 1.13% | 52.1235% | 0.401981 s |
| BBM-label-free-B32 | 250/250 | 1/250 (0.4%) | 10.2365% ± 0.593% | 23.0535% | 0.298565 s |
| SE-agglomerative | 250/250 | 44/250 (17.6%) | 1.76361% ± 0.268% | 11.4561% | 0.000271796 s |

## Audit interpretation

- The equal-candidate comparison is NEST-coalescent-B32, not NEST-R32: both use exactly 32 candidates. The three additional deterministic starts in NEST-R32 do not change any selected endpoint on this split.
- NEST is exact on 249/250. Its sole miss is `clean` seed 168: optimum 1.656298994143 bits, selected 1.657622313993 bits, a 0.07990% gap.
- Against NEST, HCSE has 0 wins / 2 ties / 248 losses; oracle BBM has 0 wins / 1 tie / 249 losses (counting failures as losses); label-free BBM has 0 wins / 1 tie / 249 losses; SE agglomerative has 0 wins / 44 ties / 206 losses.
- HCSE produces only 1--3 distinct entropies across its 32 calls (mean 2.112), so repeated calls mostly repeat a deterministic constructor rather than explore 32 basins.
- Oracle BBM fails on two full instances because all 32 calls raise `Cheeger cut: Graph should not be empty!`: imbalanced seed 177, weak-hierarchy seed 197. Its gap statistics therefore use 248 valid instances, while the exact-hit rate retains all 250 in the denominator.
- This is finite-suite evidence. It does not prove a worst-case approximation ratio or success probability on arbitrary graphs.

## Reproduction

```bash
MPLCONFIGDIR=/tmp/selib_mplconfig .venv/bin/python scripts/run_nni_restart_fairness.py --output results/nni_restart_fairness.json --seed-start 160 --seeds 50 --budget 32
.venv/bin/python scripts/verify_nni_restart_fairness.py
```
