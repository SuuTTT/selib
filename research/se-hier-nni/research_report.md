# Research Report: NEST

## Method

NEST builds SE-agglomerative, recursive-SE, and optional Paris candidate
hierarchies, then refines each with exact rooted nearest-neighbor interchange
(NNI). For `((A,B),C) -> (A,(B,C))`, the full structural-entropy change depends
only on two cross-module weights and three module volumes. Every selected move
is also checked against an independent full-objective recomputation.

After exact one-step descent, a bounded compound stage may cross a controlled
first-step barrier but commits only a lower-entropy two-step endpoint. A fixed
eight-node witness goes from a strict one-NNI local optimum of `1.970038` bits
to `1.920593` bits.

## Global certificate

By the known binary-sufficiency result, inserting a binary module beneath any
multiway node changes entropy by
`-2 W(A,B) / vol(V) log2(V_P/V_(A union B))`, which is nonpositive. Thus some
binary refinement is at least as good as every multiway tree. We re-derive this
identity only for completeness. An unordered arbitrary-subset dynamic program,
specialized from generic cluster-trellis inference,
consequently computes the true global optimum over all encoding trees in
`O(3^n)` time and `O(2^n)` memory.

The first exact audit uses five 12-vertex HSBM regimes and ten seeds per regime.
Standard NEST is globally optimal on 45/50; mean relative gap is 0.118% and the
maximum is 3.72%. Earlier phased restart splits yielded 800/800 hits after
calibration. A stricter new sealed comparison instead gives NEST, HCSE, and BBM
the same 32-candidate budget on 250 fresh graphs and retains every candidate.
NEST reaches 249/250 optima (sole gap 0.07990%), versus 2/250 for HCSE and
1/250 for either BBM variant. This newer comparison is the manuscript result.
It is a finite-family certificate, not a general approximation ratio.

## Frozen external evidence

- Main artifact: 350 method records over 50 paired 64-vertex HSBMs.
- NEST has lower entropy than HCSE and BBM on all 50 graphs and the lowest mean
  entropy in every regime.
- Four bundled real networks add 28 records; NEST is the raw-objective winner
  on all four.
- A 250-record ablation separates candidate-pool, one-step NNI, and compound
  gains and exactly matches the main artifact.
- The operator audit shows that SE agglomeration, Paris, HCSE, and BBM can leave
  exact NNI or two-step improvements.

## Submission state

The paper is framed solely around NEST; the earlier general-edit method is not
presented. The official TAMC page requires double-blind LNCS submission. Final
page-count, font, render, checker, hashes, and human EasyChair attestations are
recorded in `SUBMISSION_READINESS.md` and `ARTIFACT_MANIFEST.md`.
