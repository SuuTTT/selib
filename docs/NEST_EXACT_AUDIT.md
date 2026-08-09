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
- **Strict planted recovery:** every declared fine and coarse planted block is
  present as the descendant-leaf set of some returned tree node. Singleton
  fine blocks are necessarily recovered and are counted explicitly.

Optimal-hit rate measures optimization quality, not recovery of a unique
planted hierarchy. Multiple different trees can tie at `H*`; use planted
fine/coarse recovery metrics separately when topology recovery matters.

## Per-start basin probability

For a fixed graph `G`, deterministic NNI refinement `F`, exact optimum `H*`,
and start distribution `mu`, the per-start objective-success probability is

```text
p_G = sum_T mu(T) 1{ H(F(T)) = H* }.
```

It is a property of that graph, start distribution, tie-breaking rule, and
refinement configuration—not a universal constant of NEST. The exact dynamic
program computes `H*`; it does not compute this basin probability.

For `n <= 8`, `scripts/run_nni_basin_audit.py` enumerates every unordered
rooted binary labeled topology. There are `(2n-3)!!` such topologies: 105,
945, 10,395, and 135,135 for `n=5,6,7,8`. It reports both:

- the uniform fraction of topologies ending at `H*`; and
- the probability induced by NEST's pairwise coalescent generator.

The latter is not uniform over topologies. If a topology has child subtrees
with `a` and `b` leaves and compatible-history counts `h(A), h(B)`, then

```text
h(T) = binom(a+b-2, a-1) h(A) h(B),
mu(T) = h(T) / product_{k=2}^n binom(k,2).
```

At `n=12`, exhaustive enumeration would require 13,749,310,575 topologies, so
the companion audit uses 10,000 independent starts per fixed hard graph and
reports exact two-sided Clopper--Pearson 95% confidence intervals. For `R`
independent random starts, the implied hit probability is `1-(1-p_G)^R`. If
the deterministic candidate pool already reaches `H*`, NEST-R succeeds before
using any random start; otherwise this expression gives its random-restart
success probability.

In the frozen audit, the hard noisy `n=8` graph has exact coalescent mass
`p_G=0.252365`, so 32 starts imply `0.999909`, not certainty. Across eight
preidentified hard `n=12` graphs, 10,000-start estimates range from `0.0807`
to `0.4643`; the hardest case implies `0.932293` for 32 starts. Strict planted
recovery occurred in none of the 80,000 sampled endpoints and has zero exact
mass on the audited `n=8` graph. This is evidence of objective--recovery
misalignment under the strict all-clades criterion, not evidence that the
generator labels or the reported NMI/purity values were fabricated.

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
python scripts/run_nni_basin_audit.py --mode exact --exact-regimes noisy \
  --exact-graph-seed 9
python scripts/run_nni_basin_audit.py --mode monte-carlo --starts 10000
python scripts/verify_nni_basin_audit.py
```
