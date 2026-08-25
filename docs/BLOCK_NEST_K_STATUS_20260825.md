# Block-NEST-K research status — 2026-08-25

## Decision

**Theory/implementation gate: pass. Method-paper gate: not yet passed.**

The exact block neighborhood is real: a certified node-local partition can be
strictly block-improvable. However, the current label-free agreement/component
proposal family produced no independent gain beyond view-diverse singleton
search in the completed synthetic screens. Pairwise merge-split found only tiny
additional H2 decreases and did not consistently improve task partitions. We
therefore do not claim a new method, SOTA, or a paper at this stage.

## What is established

- Sparse spectral initialization now works beyond the former `n <= 3000`
  cutoff without dense adjacency materialization.
- Fixed-K state retains nonempty zero-volume communities correctly.
- Exact block scoring supports weighted graphs and self-loops.
- 100,000 random checks: maximum delta error `6.217e-15`.
- 184,560 exhaustive checks: maximum delta error `3.109e-15`.
- A 10-node witness is singleton-local but has a two-node improving block with
  delta `-0.0738726643`.
- The complete existing SELib suite plus new tests passes remotely.

## Mechanism results

At `n=1000, K=3`, medium/medium conflicting views, and 75% fragmentation,
seed 0:

| Method | H2 | NMI | ARI | Time ratio vs SparseInit |
|---|---:|---:|---:|---:|
| SparseInit-NEST | 9.130745 | 0.0342 | 0.0327 | 1.00x |
| View-diverse node | 9.092089 | 0.9108 | 0.9468 | 2.18x before merge-split |
| + supplied blocks | 9.092089 | 0.9108 | 0.9468 | same output |
| + pairwise merge-split | 9.091781 | 0.8791 | 0.9263 | 4.53x |

The best block restart accepted zero block moves. Merge-split improved H2 by
only `0.000309` (about 0.0034%) and reduced NMI/ARI.

In 12 `K=6` screens (three alignment regimes, two fragmentation levels, two
seeds), block versus view-diverse H2 improved in `0/12` conditions and the best
restart accepted a block in `0/12`.

At `K=6`, weak/weak conflict and 75% fragmentation, merge-split improved H2 by
only `0.000279` (about 0.0031%), reduced NMI/ARI by about `0.009`, and required
`6.14x` SparseInit wall time.

## Five-seed conflict/null finding

For equal-strength but incompatible topology and feature partitions, assigning
the feature partition as the single “truth” is not identifiable from unlabeled
inputs. At 75% fragmentation, view-diverse exact-H2 selection produced a mean
H2 change of `-0.007989` but a mean NMI change of `-0.000698`: large positive
and negative seed-level changes cancel because the selected lower-H2 solution
can correspond to either valid view. One seed changed from NMI `0.8996` to
`0.0016` while lowering H2 by `0.001054`.

This condition must be reported as a view-ambiguity/null test, not as evidence
that one unlabeled partition should recover the arbitrarily designated view.

## Next research gate

Do not scale the present block proposal family to the full benchmark. The next
candidate must address view ambiguity explicitly and without labels. A viable
direction is a cross-fitted predictive/MDL selector that either:

1. returns a Pareto set when topology and feature evidence are statistically
   indistinguishable; or
2. selects one partition only when held-out multi-view predictive evidence
   passes a preregistered Bayes/description-length gate.

It must first beat view-diverse singleton search on exposed synthetic and real
development data, with `<3x` wall time, before any untouched confirmation.
