# A Practitioner's Guide to Structural Entropy: What Works, What Doesn't

> Structural entropy (SE) is a hierarchy-discovery and graph-uncertainty measure, not a
> drop-in accuracy booster. Whether it helps depends on the *regime*. This guide distills
> the lessons from a decade of SE work and from our own empirical re-runs (the
> [SE benchmark](https://github.com/SuuTTT/structural-entropy-benchmark)) into a decision
> guide: when to reach for SE, when not to, and the traps that waste people's time.

The single most important finding across everything we tested: **the value of structural
entropy is regime-dependent.** SE is strong where a *hierarchy or an entropy value is itself
the deliverable*, and merely *complementary* (or irrelevant) where you only want a flat label
or a prediction score. Use the table below as a triage, then read the lesson that applies.

## TL;DR decision table

| Your goal | Does SE help? | Use |
|---|---|---|
| Recover a **hierarchy / dendrogram** of a graph | **Yes — SE's home turf** | `selib` hierarchical optimizer; compare on Dasgupta cost **and** label recovery |
| **Hierarchical graph pooling** for graph classification | **Yes, reliably** | SEP-style: one global encoding tree → pooling levels |
| **Graph structure learning / denoising** (clean a noisy adjacency) | **Often** (dataset-dependent) | SE-GSL-style rewiring along the SE backbone |
| **Flat community detection** (just want the partition) | **Complementary, not dominant** | Try SE *and* Louvain/Leiden/Infomap; often a classical baseline wins or ties |
| **Plain node/graph classification accuracy** | **Usually no SE-specific gain** | A random tree of the same shape often matches the SE tree — don't assume the tree is doing the work |
| **RL state/skill abstraction** | **Sometimes** — needs a clean hierarchy + non-sparse reward | Validate per-task across seeds before trusting it |
| **LLM uncertainty quantification** | **Yes, if implemented faithfully** | π-weighted (stationary-distribution) SE over an NLI semantic graph |

## What genuinely works (and why)

**1. Hierarchy is the product.** When the deliverable *is* a multi-level tree, SE shines. In
our re-runs SE-based hierarchical clustering places first or tied-first on most synthetic
benchmarks, and SE-guided pooling (SEP) reproduced its reported accuracy on **all seven TU
datasets**, beating learned-pooling baselines (DiffPool, MinCutPool, DMoN) on the chemically
structured graphs (PROTEINS, NCI1). *Why:* a single global encoding tree gives a coherent
multi-scale assignment that local, greedy methods can't, and minimization picks the depth so
you don't tune a resolution knob.

**2. SE as a structural prior for denoising.** SE-GSL-style structure learning reproduced on
node classification (Cora 0.87–0.89 across GCN/GAT/SAGE). *Why:* noise raises SE, so the
minimal-SE skeleton is the graph's low-uncertainty signal.

**3. LLM uncertainty — if you implement it faithfully.** SE over a semantic-entailment graph
of sampled generations is a strong black-box uncertainty signal, **but only with the faithful
formulation** (directed NLI graph → transition matrix → stationary distribution π → π-weighted
SE). The naive degree-based version underperforms and was the source of false negatives.

## What does NOT work (the expensive lessons)

**1. "The SE tree must be why it works" — often false.** For graph *classification*, replacing
the SE encoding tree with a **random tree of identical shape** frequently matches accuracy,
even though the SE tree's communities are 3–4× more cohesive. SE structure can be real and
yet *irrelevant to the label* if the readout is structure-blind (e.g. sum-pooling). **Always
run the random-tree / random-partition control** before claiming the hierarchy is load-bearing.

**2. Lower SE ≠ better labels.** Minimizing SE does not maximize community recovery (NMI/ARI);
the two can diverge. If your target is a *flat partition*, evaluate label recovery directly,
and don't assume the lowest-SE solution is the best one.

**3. Dasgupta cost is gameable.** When benchmarking hierarchies, a degenerate caterpillar/chain
dendrogram can achieve the *lowest* Dasgupta cost while recovering essentially no structure
(NMI ≈ 0). **Never report Dasgupta cost alone** — pair it with community recovery.

**4. Flat community detection: classical baselines stay strong.** On LFR across the mixing
parameter, Louvain/Leiden/Infomap are hard to beat. SE is complementary here, not a clear win.

**5. RL abstraction is not automatic.** SE state/skill abstraction (SISA, SISL) gave *null*
results at modest compute in our reproductions — it helps when the task has a genuine
hierarchy and the reward is not too sparse, and needs enough demonstrations/training before
the prior pays off. Validate per task, across seeds.

**6. Reproducibility trap: released code ≠ the paper.** Several SE repos drift from their
papers (wrong NLI model, missing stationary distribution, a degenerate K=1 case). If results
look wrong, check faithfulness against the equations before concluding the method fails.

## Practical engineering notes

- **Cost.** The classic combinatorial SE builders are roughly **O(n²)** and CPU-bound; they
  stall on graphs of a few thousand nodes. For large graphs use a multilevel / sampling
  optimizer (`selib`), and keep `numba` installed (a stripped/`numpy>=1.24`-incompatible build
  silently falls back to a hopeless pure-Python loop).
- **Pick the dimension deliberately.** 1D SE ≈ degree entropy (a global scalar); 2D SE = a
  flat partition's coding cost; the full kD encoding tree = the multi-scale hierarchy. Use the
  smallest that matches your question.
- **The graph you feed it is everything.** SE only measures the structure you give it. For
  semantic/LLM uses, an embedding-cosine graph over verbose text is nearly uniform and useless;
  an NLI-entailment graph discriminates. Garbage graph → garbage SE.
- **Controls to run by default.** (i) shape-matched random tree, (ii) random-partition with the
  same objective, (iii) for hierarchies, report cost *and* recovery, (iv) multiple seeds.

## Where to go next
- **Use it:** `selib` — compute, optimize, and benchmark SE under one API (see the README).
- **Compare it:** the [SE benchmark](https://github.com/SuuTTT/structural-entropy-benchmark)
  has the per-run artifacts behind every claim above.
- **Understand the method space:** the survey's taxonomy maps each SE method to its task.
