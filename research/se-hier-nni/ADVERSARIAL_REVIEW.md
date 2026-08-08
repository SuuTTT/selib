# Adversarial pre-submission review

Review date: 2026-08-08. Target: TAMC 2026. Decision gate: **PASS TO
SUBMISSION**, subject only to the non-simultaneous-submission attestation in
`SUBMISSION_READINESS.md`.

## Reviewer summary

The paper derives an exact local structural-entropy change for rooted NNI,
turns it into monotone one-step refinement with a checkable local certificate,
adds a safe bounded two-step escape, and replaces the prior expensive generic
tree-edit stage with a multi-start NNI optimizer. The main contribution is not
NNI itself; it is the structural-entropy-specific identity, verified optimizer,
and constructor audit.

## Correctness audit

- Re-expanded the old and new local entropy contributions independently. After
  substituting `g_(A union B)=g_A+g_B-2W(A,B)` and the analogous identity for
  `B union C`, all boundary terms telescope and exactly Eq. (3) remains.
- The theorem now states the positive local-volume condition explicitly and
  handles zero-volume modules by their zero-contribution limit.
- The one-step proposition is correctly limited to eligible binary edges and
  termination before a move-budget cap; it does not imply global optimality.
- The compound proposition claims only monotone accepted endpoints and
  existence of an escaped witness, not complete depth-two search.
- The merge--compress proposition is exact: contracting the old sibling module
  has nonnegative entropy change, inserting the new sibling module has
  nonpositive change, and their sum is the NNI delta. Its conclusion is limited
  to separation from monotone single-primitive search; a full HCSE
  stretch--compress round may cross the same intermediate barrier.
- More than 100 random weighted moves agree with independent full-objective
  recomputation to `1e-9`; every accepted benchmark endpoint is rescored.

No fatal proof error was found.

## Novelty audit

The closest checked works are HCSE/BBM, Jowhari's interchange local search for
the different Dasgupta/Moseley--Wang objective, Paris, and HypCSE. None derives
or implements exact rooted-NNI refinement for the discrete weighted-graph
structural-entropy objective. Searches of current arXiv, PMLR, and AAAI primary
records found no closer result. The manuscript avoids claiming invention of
NNI, structural entropy, or local search in tree space.

## Evidence audit

- 350 frozen main records: seven methods, five HSBM regimes, ten paired seeds.
- 28 real-network records, 24 clean scaling records, and 250 ablation records.
- The proposed method is the raw-entropy winner on 50/50 synthetic graphs and
  4/4 bundled real networks; scaling improves 12/12 paired runs.
- Recovery is reported separately from the optimized objective, and BBM's
  planted `k` advantage is marked.
- The paper does not infer an asymptotic speed theorem from the small scaling
  suite.

## Remaining weaknesses, already bounded in the paper

1. The empirical graphs are modest in size. The paper therefore claims only a
   measured speedup over the prior implementation, not large-scale or
   hardware-independent complexity.
2. A one-NNI certificate is local, and compound search is beam/barrier limited.
3. NNI leaves unresolved multiway regions to the constructor.
4. The method optimizes structural entropy; it does not promise improvement in
   every external hierarchy metric.

These limitations reduce claim breadth but do not invalidate the TAMC
algorithm/information-theory contribution.

## Double-blind and overlap gate

The PDF contains anonymous author/affiliation fields, no acknowledgements, no
repository URL, and no explicit self-identification. Self-related work is cited
in the third person. The Local-Traps/clique manuscript must not be under review
simultaneously if it contains essentially the same NNI identity or results;
this submission owns the arbitrary-weight optimizer and its evidence, while
the other draft owns special clique-landscape analysis.
