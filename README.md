# selib

**A standardized library for structural entropy** — compute it, optimize it, and
benchmark structural-entropy (SE) methods against classical baselines under one API.

`selib` grew out of an empirical re-appraisal of the SE literature (see the
[benchmark](https://github.com/SuuTTT/structural-entropy-benchmark) and
[survey](https://github.com/SuuTTT/structural-entropy-survey-paper)). The repeated
pain there was that every SE paper ships its own data loader, its own metric, and
its own (often unmaintained) code, so "does SE actually help?" was hard to answer
on equal footing. `selib` fixes the *interface*: one `Method.fit_predict(G, k, seed)`
contract, shared datasets and metrics, and a one-call benchmark — so an SE method
and a Louvain baseline are scored exactly the same way.

## SE calculator

A first-class entry point for *computing* structural entropy (separate from the
optimizers), plus a [gallery](https://suuttt.github.io/selib/gallery.html) of
SE-optimal partitions on classical graphs:

```python
import selib, networkx as nx
G = nx.karate_club_graph()

selib.se_report(G)                     # {n, m, se_1d, se_2d_optimal, num_communities, se_tree_optimal, ...}
selib.structural_entropy(G, dim=1)     # 1D structural entropy (partition-free upper bound)
selib.structural_entropy(G)            # optimal 2D structural entropy (minimized over partitions)
labels, h2 = selib.optimal_2d(G)       # the SE-optimal partition and its 2D-SE
selib.structural_entropy(G, labels)    # 2D-SE of any given partition
tree, hT = selib.optimal_tree(G)       # the SE-optimal encoding tree and its H^T
selib.structural_entropy(G, tree=tree) # H^T of any encoding tree
```

## What's in v0.1

- **Uniform method registry.** Every algorithm — SE or baseline — is a `Method`
  with metadata (`is_se`, `native`, `paper`, `repo`) and a single `fit_predict`.
- **Native SE core** (`selib.se`): greedy 2D-structural-entropy encoding tree
  (`se_agglomerative`) + Dasgupta cost. Dependency-light; the seed of a fuller
  encoding-tree + differentiable-SE engine.
- **`se_louvain` — the recommended SE minimizer** (`selib.seopt`): a Louvain-style
  multilevel optimizer of the *same* 2D-SE objective (local node moves + community
  aggregation + multistart, exact O(degree) move delta). The merge-only
  `se_agglomerative` gets stuck in poor local optima; `se_louvain` reaches lower
  structural entropy on every benchmark graph and substantially higher community-
  detection accuracy. Validated against the canonical metric and brute-force
  exhaustive optima (gap 0.000 on small graphs). See the
  [benchmark page](https://suuttt.github.io/selib/).
- **`se_hier` — hierarchical (encoding-tree) SE optimizer** (`selib.htree`):
  structural entropy is defined over an *encoding tree*, not just a flat partition.
  `se_hier` builds a multilevel tree (binary dendrogram + recursive `se_louvain`
  inits) and refines it with exact-guarded local moves (collapse a level, relocate a
  subtree), accepting only moves that strictly lower the exact tree structural
  entropy H^T. Result is ≤ the naive binary dendrogram by construction, and strictly
  lower on every benchmark graph. Validated: a 2-level tree's H^T equals the
  canonical 2D-SE exactly, and refinement is monotone. It warm-starts from several
  constructions — including Paris (scikit-network) when available — and refines the
  best, so it is ≤ each of them by construction.

- **`se_gnn` — attribute-aware SE** (`selib.segnn`, ported from the author's glass-jax
  prototype): a small GCN trained end-to-end to minimize a **differentiable soft 2D
  structural entropy**, with a **balanced Sinkhorn assignment head** (default) that
  prevents the cluster collapse a plain softmax suffers under pure SE minimization.
  The soft objective at a hard (one-hot) assignment equals the canonical 2D-SE exactly
  (validated). Needs `jax` (CPU is fine: `pip install jax "numpy<2"`); node features are
  read from `G.graph["X"]` (the bundled `Cora`/`Citeseer` Planetoid loaders attach them).
  Cora: NMI 0.487 / ARI 0.387 / ACC 0.592 at k = 7 — beats every topology-only method on
  all three metrics and matches LSENet, with a far smaller model. A config sweep
  (`scripts/sweep_segnn.py`) shows the default (2-layer, hidden 64) is best on Cora;
  width + feature `dropout` helps the sparser-feature Citeseer (NMI 0.262→0.316). The
  residual gap to DeSE (0.579 on Cora) is architectural — deeper/hyperbolic encoders —
  not a matter of tuning; `dropout=`/`layers=`/`hidden=` are exposed for experimentation.

**Comparison with existing work** (see the [benchmark page](https://suuttt.github.io/selib/),
section 0c): on identical graphs, `se_louvain` reaches the lowest 2D structural
entropy of all methods including the published **CoDeSEG** (its original C++ code, run
through selib's wrapper); `se_hier` reaches the lowest encoding-tree structural entropy
of all, including Paris and the binary SE dendrogram. On attributed graphs (Cora/Citeseer/
Photo) feature-aware SE methods (DeSE/LSENet) are shown vs. topology baselines — selib
v0.1 is topology-only, which motivates attribute-aware SE as future work.
- **Baselines** (native): Louvain, Leiden, Infomap, spectral clustering.
- **Drop-in wrappers** over published SE methods' *original* code (deDoc jar,
  CoDeSEG binary, …). selib doesn't vendor upstream code; point it at the artifact
  via an env var and the wrapper runs the paper's real implementation. If unset it
  raises a clear `ExternalNotConfigured` with the repo URL — the API stays uniform
  whether or not the upstream is installed.
- **Shared datasets & metrics**: LFR/SBM generators, Karate/Football, plus ARI/NMI
  *and* cross-objective scores (modularity, map-equation codelength, 2D-SE) so
  methods optimizing different objectives are still comparable.
- **One-call benchmark**: `selib.benchmark(methods, datasets) -> tidy records`.

## Install

```bash
pip install -e .              # core (networkx/numpy/scipy/scikit-learn)
pip install -e ".[extra]"     # + leidenalg/igraph/infomap for those baselines
```

## Quick start

```python
import selib

selib.list_methods()                      # ['infomap','leiden','louvain','se_agglomerative','spectral', ...]
selib.info("se_agglomerative")            # metadata: paper, is_se, native, ...

recs = selib.benchmark(
    ["louvain", "leiden", "se_agglomerative"],
    ["Karate", "SBM-Clean", "SBM-Noisy"],
)
selib.summarize(recs, "nmi")                   # {dataset: {method: mean NMI}}
selib.summarize(recs, "structural_entropy_2d") # same, on the 2D structural-entropy objective
```

### Running a wrapped SE method on its original code

```bash
export SELIB_DEDOC_JAR=/path/to/deDoc.jar          # github.com/yinxc/structural-information-minimisation
export SELIB_CODESEG_BIN=/path/to/codeseg          # github.com/SELGroup/CoDeSEG
```
```python
selib.benchmark(["dedoc", "codeseg", "louvain"], ["SBM-Clean"])
```

## Registering your own method

```python
import selib

@selib.method("my_se", family="community_detection", is_se=True, native=True,
              paper="...", note="my encoding-tree variant")
def my_se(G, k=None, seed=0):
    ...                                    # return a list[int] of node labels
    return labels
```

## API surface

| call | purpose |
|------|---------|
| `selib.list_methods(family=, se_only=, native_only=)` | available algorithms |
| `selib.get(name)` / `selib.info(name)` | the `Method` / its metadata |
| `selib.method(...)` / `selib.register(...)` | add your own |
| `selib.benchmark(methods, datasets, seeds=, cross_objective=)` | run the grid |
| `selib.summarize(records, metric)` | `{dataset: {method: mean}}` |
| `selib.se`, `selib.metrics`, `selib.datasets` | core + shared utilities |

## Status & roadmap

v0.1 standardizes the *interface* and ships the native SE core + community-detection
methods. Next: a full encoding-tree data structure with $k$-D structural entropy, a
differentiable SE objective for structure learning, and first-class wrappers for the
deep SE methods (SEP, SE-GSL, SEGA, LSENet, DeSE) over their pinned environments.

## License

MIT.
