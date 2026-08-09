# Novelty audit: SE--NNI

Audit date: 2026-08-08. Scope: exact discrete hierarchy optimization for the
full structural-entropy objective on a fixed undirected weighted graph.

## Closest checked work

| Work | What it contributes | Why it does not subsume this paper |
|---|---|---|
| Zhang, Wang, and Li, Genome Biology 2021 (SuperTAD) | Proves binary sufficiency for minimum structural entropy and gives contiguity-constrained dynamic programs for hierarchical TADs. | Binary sufficiency is prior art and is only restated here. Our audit uses arbitrary graph subsets; the core method contribution is exact NNI refinement and certification. |
| Pan et al., UAI 2025 (HCSE/BBM) | Structural-entropy hierarchy construction via partition/merge and stretch/compress; approximation results in special graph regimes. | It does not derive the NNI delta, certify NNI-local output, or run bounded two-move escape on an arbitrary returned tree. |
| Jowhari, arXiv:2405.15983 | Interchange local search and an implementation for Dasgupta cost / Moseley--Wang revenue. | Its linear cardinality-weighted objective is different from nested graph structural entropy; its local delta cannot be reused for Eq. (1). |
| Zeng et al., AAAI 2026 (HypCSE) | Differentiable hyperbolic relaxation of structural entropy plus graph-structure learning from features. | It changes/learns the graph and optimizes a continuous relaxation; this paper exactly refines a discrete tree on one fixed weighted graph. |
| Bonald et al., NeurIPS 2018 (Paris) | Fast agglomerative graph dendrogram. | Paris is one initializer here; it provides neither an SE-specific NNI identity nor an SE-locality certificate. |
| Macaluso et al., AISTATS 2021 (Cluster Trellis); Greenberg et al., UAI 2021 (A*) | Generic exact and approximate inference over binary hierarchical clusterings using subset trellises. | The subset-DP pattern is prior art. Using prior binary sufficiency, this paper contributes an SE-specific arbitrary-subset recurrence/audit, not generic exact-HC inference. |
| {\'A}goston and E.-Nagy, CEJOR 2024; G{\'o}recki et al., BMC Evol. Biol. 2020 | Percentage of heuristic runs reaching an exact optimum in k-means and median-tree search. | Optimal-hit rate is an established optimization diagnostic adopted here, not a newly invented metric. |

## Defensible novelty statement

The checked literature supports a narrow first-of-kind claim: an exact
weighted structural-entropy delta for rooted NNI used as a verified discrete
optimizer, coupled with a one-NNI certificate, safe bounded two-step escape,
and a fast multi-start implementation. The paper must not claim to invent NNI,
local search for hierarchical clustering, or structural-entropy hierarchy
construction. It must also not claim generic subset dynamic programming or
exact-optimum hit rate as new.

## Evidence and remaining risks

- The exact identity has a direct telescoping proof and agrees with full
  objective recomputation on more than 100 random weighted moves.
- A new atomic-separation proposition decomposes every local NNI into HCSE-style
  compression followed by merging. The compression loss is always nonnegative,
  while the later merge gain can be larger. Therefore an improving NNI can be
  inaccessible to any monotone single merge/compress step. This is a strict
  neighborhood result, not a claim that NNI dominates a complete HCSE round.
- The full method is best on 50/50 frozen HSBM graphs and 4/4 bundled real
  networks under the common exact objective.
- Component ablation confirms separate gains from the candidate pool,
  one-step NNI, and compound escape.
- NEST-R32 reaches 800/800 exact optima in the declared n=12 audit, including
  250/250 under disjoint regime RNG streams. This is finite-suite evidence, not
  a global guarantee for arbitrary graphs.
- Official BBM contains iterative eigensolver/set-order variability; the raw
  frozen artifact preserves the realized runs, but exact BBM reruns may differ
  despite resetting Python and NumPy seeds. This does not affect our method's
  deterministic repeat or the exact objective verifier.
- HypCSE is discussed as related work rather than inserted into the fixed-graph
  table because it consumes feature data, learns a graph, and optimizes a
  continuous surrogate; treating its published numbers as directly comparable
  would be misleading.

## Sources checked

- https://proceedings.mlr.press/v286/pan25a.html
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7831269/
- https://arxiv.org/abs/2405.15983
- https://ojs.aaai.org/index.php/AAAI/article/view/40035
- https://proceedings.neurips.cc/paper/2018/hash/6b180037abbebea991d8b1232f8a8ca9-Abstract.html
- https://proceedings.mlr.press/v130/macaluso21a.html
- https://proceedings.mlr.press/v161/greenberg21a.html
- https://link.springer.com/article/10.1007/s10100-023-00881-1
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7593691/
