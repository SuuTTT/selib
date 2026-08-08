# Research Report: NEST

## Baseline

Entropy-Guided Tree Editing (EGTE; artifact key `se_hier`) generates several
candidate encoding trees, including an
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

## Implemented after the pilot

- Cached descendant sets are reused within each NNI sweep.
- `refine_nni_compound` evaluates bounded two-step paths, permits a controlled
  first-step barrier, and commits only a fully verified lower endpoint.
- A fixed eight-node witness starts at a strict one-NNI local optimum of
  `1.970038` bits and reaches `1.920593` bits through compound search.
- `encoding_tree_nni_fast` refines SE-agglomerative, recursive-SE, and Paris
  candidates without the expensive generic collapse/relocation stage.
- The frozen benchmark compares seven methods over five two-level HSBM regimes
  and ten seeds, plus a separate real-network suite.

## Frozen evidence completed

- The main artifact has 350 verified records over 50 paired graphs; the new
  method is the raw-objective winner on all 50.
- Four bundled real networks add 28 verified method records; the new method is
  the raw-objective winner on all four.
- Clean scaling over 32--128 vertices and three seeds per size gives lower
  entropy on 12/12 pairs and a 9.7--22.2x speedup of NEST over EGTE.
- A 250-record component ablation separates the candidate-pool, one-step NNI,
  and compound-search gains and exactly matches the main artifact.
- Current HCSE, Jowhari local search, and HypCSE papers were checked to delimit
  the novelty claim. HypCSE is not reported as a direct baseline because it
  learns a graph from feature data and optimizes a continuous relaxation.
- The LNCS manuscript compiles to the 12-page limit with generated figures and
  tables.

## Submission state

The official TAMC page now explicitly confirms double-blind review, so the
anonymous author/affiliation fields are correct. The final A4/page/font/render
audit has been run on the exact 12-page PDF; all fonts are embedded and no
Type 3 fonts are present. The double-blind TAMC checker passes with zero
failures, and an adversarial proof/novelty/claim read passes the paper to
submission.

The remaining actions occur privately in EasyChair: enter the real author
metadata and corresponding author, attest that no essentially overlapping
paper is simultaneously under review, and retain the upload receipt and
checksum. See `SUBMISSION_READINESS.md`.
