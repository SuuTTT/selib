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
  canonical 2D-SE exactly, and refinement is monotone.
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
