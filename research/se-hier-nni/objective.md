# Objective: NNI-Certified Structural-Entropy Hierarchies

Build and evaluate a hierarchical graph-clustering algorithm that refines a
fast pool of SE-agglomerative, recursive-SE, and Paris starts with exact rooted
NNI, and uses a bounded compound-move escape only when strict one-step search
stalls. The released `se_hier` is a required baseline, not a mandatory slow
stage of the new method.

## Primary claim target

The final method should return an encoding tree no worse than each of its own
refined starts, reach a certified one-NNI local optimum, and improve the
entropy--runtime frontier relative to the released `se_hier` and the strongest
reproducible hierarchy baselines. A slower compatibility variant additionally
refines the final `se_hier` output and is no worse than that identical start.

## New-paper boundary

This is a separate method paper. The existing curvature/clique manuscript is
not rewritten and its source is not copied here. If both papers are submitted,
the older manuscript's clique trap and curvature theorem must be cited or
disclosed as related work, not reclaimed as new. New contributions here are:

1. the use of the exact weighted-graph NNI identity as a verified optimizer;
2. one-NNI certification and fast multi-start hierarchy construction;
3. cached evaluation and bounded compound escape;
4. comparison against HCSE, BBM, Paris, HypCSE when reproducible, and the
   unmodified SELib optimizer.

If the two manuscripts cannot be cleanly separated under a venue's concurrent
submission policy, submit only one or delay the method paper.

## GO conditions

- Predicted NNI deltas match independent full `H^T` recomputation.
- The enhanced method never worsens `H^T` for identical starts.
- At least one meaningful baseline family is improved consistently across
  held-out graph seeds, not only on a hand-built trap.
- Runtime and memory remain practical relative to current `se_hier`.

## NO-GO conditions

- Improvements disappear on held-out seeds or larger graphs.
- Lower `H^T` is obtained only by producing unusably deep trees without better
  hierarchy recovery.
- NNI duplicates an existing operator after exact neighborhood comparison.
- The method cannot be distinguished from the concurrently submitted theory
  manuscript without reusing its central theorem as a new claim.
