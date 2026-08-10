# NEST scaled audit protocol (2026-08-10)

This audit expands the paper evidence without changing the method, tuning on
the exact optimum, or touching the earlier sealed artifacts.

## Frozen suites

| Suite | Graphs | Size | Purpose |
|---|---:|---:|---|
| paired HSBM | 500 (5 regimes x 100 fresh seeds) | 64 | narrow the paired performance confidence intervals |
| exact-B32 | 1,000 (5 regimes x 200 fresh seeds) | 12 | estimate exact-optimum hit probability under a fixed 32-start budget |
| exact-B32-size14 | 100 (5 regimes x 20 fresh seeds) | 14 | test whether the exact result survives a larger search space |
| exact-B32-size16 | 25 (5 regimes x 5 fresh seeds) | 16 | limited exponential-DP stress test |

For the n=14 and n=16 suites, each regime's native six-block size vector is
resized by deterministic largest-remainder proportional allocation.  This
preserves the imbalanced regime's unequal block structure instead of replacing
all regimes with one shared size vector.

The paired HSBM suite compares the same seven constructors/refinements already
used by the paper.  The exact suites compare NEST, random-coalescent NEST,
HCSE, oracle-k BBM, label-free BBM, SE agglomeration, and Louvain.  Every
candidate is selected using structural entropy; the exact optimum is read only
after selection.  All graph and restart seed ranges are disjoint from the
earlier audit.

## Resource guardrails

- target: already-running Vast instance 45525865 only;
- eight single-core processes pinned to cores 0--7;
- `nice -n 15` and idle-class `ionice`;
- one BLAS/OpenMP thread per process;
- 8 GiB virtual-memory ceiling and 12-hour timeout per process;
- atomic JSON checkpoint after every graph;
- no GPU calls, paid APIs, instance lifecycle operations, or changes to the
  existing GPU queue;
- copy JSON, logs, status files, and SHA-256 manifests off the worker before
  treating any result as paper evidence.

## Statistical reporting gate

Do not replace the abstract numbers merely because the sample is larger.
First verify protocol identity, graph counts, finite outcomes, hash manifests,
paired seed coverage, and baseline failure rates.  Report paired differences
with 95% confidence intervals and exact-hit rates with binomial confidence
intervals.  Keep the statement that exact-instance evidence does not imply a
general approximation ratio.
