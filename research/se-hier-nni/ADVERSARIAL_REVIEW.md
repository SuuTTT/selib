# Adversarial pre-submission review

Review date: 2026-08-10. Target: TAMC 2026. Decision gate: **PASS TO
SUBMISSION, SUBJECT TO HUMAN AUTHOR ATTESTATIONS**.

## Reviewer summary

The paper derives an exact local structural-entropy change for rooted NNI,
turns it into monotone refinement with a checkable local certificate, adds a
safe bounded two-step escape, and proposes the multi-start NEST optimizer. Its
global-audit component uses prior binary sufficiency and specializes an
exponential cluster-trellis recurrence to structural entropy over arbitrary
vertex subsets.

## Correctness audit

- Re-expanding the old and new local contributions gives the stated NNI delta;
  more than 100 random weighted moves match full rescoring to `1e-9`.
- One-step and compound guarantees are correctly limited to accepted endpoints
  and the declared finite neighborhoods.
- Inserting a binary union of siblings changes entropy by
  `-2W(A,B) log2(V_P/V_S)/vol(V) <= 0`, so repeated insertion proves binary
  sufficiency.
- The subset recurrence enumerates each unordered root split and includes the
  two child-to-parent contributions. It uses `O(3^n)` time and `O(2^n)` memory.
- The DP rebuilds a tree with the same objective, matches independent
  enumeration of all 105 rooted binary trees for a five-node graph, and never
  exceeds NEST on the exact audits.
- The edge-LCA lower bound is independently checked below every exact optimum.

No fatal proof error is currently known. A human coauthor should still inspect
the binary-sufficiency re-derivation and new DP proof before upload.

## Evidence audit

- 350 frozen main records: seven internal artifact methods, five HSBM regimes,
  ten paired seeds. The paper reports NEST and five external methods only.
- NEST beats HCSE and BBM on 50/50 n=64 graphs and wins 4/4 bundled real
  networks by the optimized objective.
- 250 ablation records isolate candidate-pool, one-NNI, and compound gains.
- The original 50 n=12 records expose five standard-pool misses (0.118% mean,
  3.72% maximum gap). The newer sealed, 32-candidate-matched audit reaches
  249/250 for NEST, 2/250 for HCSE, and 1/250 for either BBM variant; all raw
  candidates are retained. The manuscript reports this stricter result and
  limits it to the audited family.

## Remaining weaknesses

1. Exact global certification is exponential and limited to n=12.
2. The universal edge-LCA lower bound is valid but loose, so it is not used to
   claim a useful large-graph approximation factor.
3. NNI-local optimality remains weaker than global optimality.
4. Structural-entropy improvement need not improve every label-based metric.
5. Main synthetic graphs are modest; large-scale behavior is not a headline
   claim in the reframed paper.

## Double-blind and overlap gate

The PDF must remain anonymous and omit repository URLs. The Local-Traps/clique
manuscript must not be simultaneously submitted if it contains essentially the
same NNI identity or evidence. This paper owns the arbitrary-weight optimizer,
SE-specific arbitrary-subset exact audit, and NEST experiments; it does not
claim the prior binary-sufficiency result.
