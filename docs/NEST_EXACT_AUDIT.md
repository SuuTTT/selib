# NEST exact-optimum audit protocol

## What the original 50 graphs are

The original audit is a small, exactly solvable diagnostic suite, not a claim
to represent all graphs. It contains **5 regimes × 10 seeds = 50 graphs**. Every
graph has 12 vertices, six fine blocks nested in three coarse blocks, and edges
sampled independently conditional on those blocks.

| Regime | Fine-block sizes | `p(same fine, same coarse, other)` | Edge weight |
|---|---|---|---|
| clean | 2,2,2,2,2,2 | 0.72, 0.25, 0.04 | 1 |
| noisy | 2,2,2,2,2,2 | 0.50, 0.30, 0.14 | 1 |
| imbalanced | 1,3,1,3,2,2 | 0.65, 0.23, 0.06 | 1 |
| weighted | 2,2,2,2,2,2 | 0.60, 0.22, 0.06 | 2/1/0.5 times LogNormal(0, 0.25) |
| weak hierarchy | 2,2,2,2,2,2 | 0.45, 0.36, 0.10 | 1 |

If a sampled graph is disconnected, consecutive sorted components receive a
stored 0.01-weight connector so structural entropy is well-defined on a
connected graph. The original protocol reused seed `s` across regimes; this
correlates some graph draws across regimes. Exact certificates for individual
graphs remain valid, but the final confirmation uses disjoint regime-specific
RNG streams to remove this dependence.

The generator is `scripts/run_nni_optimality.py::small_hierarchical_sbm`.
Result rows store their probabilities, block sizes, graph seed, and connector
edges. New regime-separated runs additionally record the effective RNG seed;
in the original protocol it is identical to the graph seed.

## Metrics

- **Additive optimality gap:** `H(T) - H*`.
- **Relative optimality gap:** `100 × (H(T) / H* - 1)`.
- **Per-instance optimal hit:** the returned objective is within
  `max(1e-9, 1e-8 × |H*|)` of the exact optimum.
- **Optimal-hit rate:** fraction of graph instances that are optimal under that
  test.
- **Stochastic success probability:** for one fixed graph and one fixed restart
  budget, fraction of independent optimizer campaigns that hit `H*`.

Optimal-hit rate measures optimization quality, not recovery of a unique
planted hierarchy. Multiple different trees can tie at `H*`; use planted
fine/coarse recovery metrics separately when topology recovery matters.

## Repair and evaluation phases

The five original misses are basin-coverage failures: widening the bounded
two-move beam does not change their endpoint, while randomized binary starts
find lower basins. NEST-R generates a random coalescent tree by repeatedly
merging two uniformly selected current components, runs the same verified NNI
descent, and keeps the lowest-entropy result. It never sees `H*` during
selection.

The restart budget was developed and evaluated in phases:

1. Development, seeds 0–9: 50 graphs.
2. Calibration, seeds 10–59: 250 graphs; this exposed misses at 16 starts and
   fixed the final budget at 32.
3. Confirmation A, seeds 60–109: 250 newly generated graphs.
4. Confirmation B, seeds 110–159: 250 graphs with disjoint regime RNG streams.

NEST-R32 hits 800/800 exact optima across these declared phases, including
250/250 in the regime-separated final confirmation. This is an empirical
finite-suite result, not a proof that 32 starts are globally optimal on an
arbitrary graph or at a larger `n`.

## Reproduction

```bash
python scripts/run_nni_optimality.py
python scripts/run_nni_restart_audit.py --output results/nni_restart_audit.json
python scripts/run_nni_restart_audit.py --skip-development --holdout-start 60 \
  --holdout-seeds 50 --output results/nni_restart_confirmation.json
python scripts/run_nni_restart_audit.py --skip-development --holdout-start 110 \
  --holdout-seeds 50 --independent-regime-seeds \
  --output results/nni_restart_independent_confirmation.json
python scripts/diagnose_nni_restart_failures.py
python scripts/verify_nni_restart_audit.py
```
