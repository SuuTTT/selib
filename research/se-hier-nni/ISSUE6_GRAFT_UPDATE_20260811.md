## Progress: certified graft closes all five frozen NEST misses

The correctness-first rooted subtree prune-and-regraft operator is now
implemented on `codex/nest-entropy-grafting`.

- 1,680 legal weighted-tree grafts preserved binary topology and one copy of
  every leaf.
- The independent edge--LCA delta agreed with complete structural-entropy
  recomputation to at most `1.41e-15` bits.
- Exhaustive best-improvement graft plus post-graft exact NNI terminated with
  no improving graft on four deterministic validation cases.
- The five preidentified sealed misses were reconstructed exactly. Applying
  the richer optimizer to each of the same 32 coalescent candidates reached
  the exact optimum on all five: clean n=12 seed 168; weak-hierarchy n=14 seed
  3004; noisy n=16 seeds 4001 and 4002; and weak-hierarchy n=16 seed 4002.

This 5/5 result is a diagnostic on known failures, not a confirmatory success
rate. The method must be frozen before a new sealed matched-neighborhood suite.

One proposed shortcut was also falsified: summing only graph edges crossing
the moved subtree is not exact, because ancestor volumes change on both graft
paths and can alter LCA contributions of edges not incident to the source.
The corrected exact formula sums changed edge--LCA terms; the next task is a
formal affected-path bucket proof and cached scorer.

Artifacts:

- `results/tcs_graft_reference_validation.json`
- `results/tcs_graft_exact_miss_diagnostic.json`
- `research/se-hier-nni/TCS_GRAFT_WORKLOG.md`
