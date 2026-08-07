# Research Report: `se_hier_nni`

## Baseline

SELib `se_hier` generates several candidate encoding trees, including an
SE-agglomerative binary dendrogram, a recursive `se_louvain` hierarchy, and
optional Paris warm starts. It refines candidates using exact-guarded level
collapse and local subtree relocation, then returns the lowest-entropy tree.

The implementation is already a plausible unpublished method contribution,
but its current candidate evaluation copies trees and recomputes full
structural entropy repeatedly. Stored SELib artifacts report lower `H^T` than
HCSE and BBM on the graphs tested, but those artifacts are not yet a
publication-grade multi-seed comparison.

## New operation

For the rooted rotation `((A,B),C) -> (A,(B,C))`, let `W(X,Y)` be the total
edge weight between modules and `V_X` their graph volume. Since only the
`A--B` and `B--C` edge classes change LCA, the exact entropy change is

```text
Delta H^T = (2 / vol(G)) * [
    W(A,B) log2(V_ABC / V_AB)
  + W(B,C) log2(V_BC / V_ABC)
]
```

This is implemented in `selib.htree.nni_delta`. Every accepted move is also
checked against an independent full `H^T` recomputation.

## Development pilot (not final evidence)

Artifact: `results/nni_pilot.json`.

- 25/25 small development runs improved the corresponding `se_hier` tree.
- Mean relative `H^T` reduction across all runs: 0.888%.
- Mean relative reductions by family: Karate 0.260%, clean SBM 0.932%, noisy
  SBM 1.158%.
- NNI changed no top-level label on Karate or clean SBM in this pilot; noisy
  SBM mean NMI and ARI both increased by about 0.0105.
- NNI refinement took about 0.002 s on Karate and 0.022--0.026 s on the
  45-node SBM cases.

These runs establish a GO decision for broader evaluation. They do not support
SOTA, scalability, robustness, or statistical-superiority claims.

## Next technical work

1. Cache module membership and inter-module weights so candidate deltas do not
   rebuild descendant sets.
2. Insert NNI before and after collapse/relocation rather than only after the
   final `se_hier` tree.
3. Add plateau traversal and bounded two-NNI compound escape.
4. Fix and test the known parent-pointer issue in `dasgupta_tree` before using
   that metric in the paper.
5. Freeze development and held-out graph seeds before full benchmarking.
