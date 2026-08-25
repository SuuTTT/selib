# selib

`selib` is a small, dependency-light Python library for computing and optimizing
structural entropy (SE) on undirected weighted graphs.  It includes flat 2D-SE
optimization, encoding-tree construction, exact local tree-edit verification,
shared evaluation metrics, and baseline adapters.

The library deliberately distinguishes three tasks:

| Task | Entry point | What is optimized / certified |
| --- | --- | --- |
| Flat partition | `selib.optimal_2d` or registered `se_louvain` | a local search of the exact 2D-SE objective |
| Fixed number of modules | `selib.se_optimize_fixed_k` | local search within the specified `K`-partition space |
| Encoding tree | `selib.optimal_tree_nni_fast` | tree structural entropy with exact NNI move checks |

`NEST` refers here to the hierarchical encoding-tree search machinery: exact
NNI deltas, bounded two-step NNI escape, subtree-graft diagnostics, and small
graph exact certificates.  These are local-search algorithms and certificates;
they do **not** claim a global optimum or state-of-the-art performance on every
dataset.

## Install

```bash
git clone https://github.com/SuuTTT/selib.git
cd selib
python -m pip install -e ".[dev]"
```

Optional classical baselines and the differentiable GNN require their respective
extras:

```bash
python -m pip install -e ".[extra]"  # Leiden, Infomap, Paris warm start
python -m pip install -e ".[gnn]"    # JAX-based se_gnn
```

## Quick start

All values below are in bits.  `labels` are aligned with `list(G.nodes())`.

```python
import networkx as nx
import selib

G = nx.karate_club_graph()

# Compute SE.
print(selib.one_dimensional(G))              # H^1(G)
labels, h2 = selib.optimal_2d(G, seed=0)     # flat 2D-SE local optimum
print(h2, len(set(labels)))

# Build a hierarchy and refine it with exact NNI deltas.
tree, h_tree = selib.optimal_tree_nni_fast(G, seed=0)
print(h_tree)

# A compact report for exploratory use.
print(selib.se_report(G))
```

### Known-K comparison

Use this only when `K` is part of the experimental condition (for example, a
controlled synthetic benchmark).  Do not obtain `K` from test labels in an
unsupervised benchmark.

```python
from selib.seopt import se_optimize_fixed_k
from selib import two_dimensional

labels = se_optimize_fixed_k(G, k=2, seed=0, starts=8)
print(two_dimensional(G, labels))
```

Experimental exact block refinement is available for research on fixed-K local
optima. Candidate blocks are proposals only; exact 2D structural entropy selects
every accepted move and restart:

```python
from selib.blockopt import se_optimize_block_fixed_k

labels, audit = se_optimize_block_fixed_k(
    G,
    k=2,
    blocks=[(1, 3), (8, 9)],  # positions in list(G.nodes())
    seed=0,
    return_audit=True,
)
assert len(set(labels)) == 2
```

See [`docs/BLOCK_NEST_K_THEORY.md`](docs/BLOCK_NEST_K_THEORY.md) and
[`docs/BLOCK_NEST_K_PREREGISTRATION.md`](docs/BLOCK_NEST_K_PREREGISTRATION.md).

### Hierarchical audit trace

```python
from selib.htree import encoding_tree_nni_fast

tree, degree, adjacency, volume, audit = encoding_tree_nni_fast(
    G, seed=0, random_restarts=4, restart_seed=17, return_trace=True
)
print(audit["selected_initializer"])
print(audit["candidate_entropies"])
```

The lower-level `refine_graft`, `graft_delta`, and `graft_delta_path` APIs are
provided for research and audit use.  They check a candidate tree edit against
the exact tree objective; see `tests/test_nni.py` for executable examples.

## Built-in methods and evaluation

```python
import selib

print(selib.list_methods())
records = selib.benchmark(
    ["louvain", "spectral", "se_louvain", "se_hier_nni"],
    ["Karate", "SBM-Clean", "SBM-Noisy"],
    seeds=range(5),
)
print(selib.summarize(records, "structural_entropy_2d"))
```

`selib.benchmark` is convenient for exploratory comparisons.  It supplies the
dataset's declared module count to methods that require `K` (such as spectral
clustering), so it is not by itself a no-label paper benchmark.  For the release
gate and its protocol, run:

```bash
python scripts/run_core_benchmark.py --output results/core_benchmark.json
```

See [the release benchmark protocol](docs/RELEASE_BENCHMARK.md) for what this
small benchmark does and does not establish.

### Latest audited core result

The completed five-seed, CPU-only remote release gate is archived with raw
records, command envelope, and checksum in
[`docs/CORE_BENCHMARK_REMOTE_20260816.md`](docs/CORE_BENCHMARK_REMOTE_20260816.md).
For the hierarchical objective $H^T$ (bits; lower is better), the fast NNI
variant was no worse than the other native hierarchy constructors on all four
release graphs while taking substantially less wall-clock time:

| Dataset | `se_hier` | `se_hier_nni` | `se_nni_fast` |
| --- | ---: | ---: | ---: |
| Karate | 2.5217 / 0.9408 s | 2.5145 / 0.9644 s | **2.4605 / 0.1239 s** |
| SBM-Clean | 3.8185 / 5.9412 s | 3.8086 / 6.0500 s | **3.6865 / 0.3136 s** |
| SBM-Moderate | 3.7732 / 6.1585 s | 3.7477 / 6.2020 s | **3.7414 / 0.2809 s** |
| SBM-Noisy | 3.8343 / 5.7701 s | 3.8107 / 5.8527 s | **3.8107 / 0.2147 s** |

These are a native regression and performance check, not a cross-paper SOTA
claim.  The full Paper B comparison is intentionally separate and uses its
own no-label, five-dataset protocol.

## Guarantees and limits

- 2D-SE and tree-SE are evaluated by the same exact scoring routines used by
  the optimizers.
- Accepted NNI and graft moves are independently rescored; tests cover weighted
  graphs and compare move deltas to complete tree re-evaluation.
- The exact dynamic program is a verifier for small graphs only (default limit:
  18 vertices), not a scalable optimizer.
- Random restarts improve local-search coverage; they are not uniform samples
  of labelled tree topologies.
- Published deep methods such as DeSE and LSENet are **not** reimplemented in
  this core package.  Their fair end-to-end comparison belongs to the separate
  Paper B protocol rather than this library release.

## Reproducibility

```bash
pytest
python scripts/run_core_benchmark.py --output results/core_benchmark.json
```

The first command is the algebra and regression gate.  The second is a compact
internal comparison across topology-only methods and synthetic regimes; it is a
merge gate, not a substitute for the planned 8–10-method × 5-dataset study.

The completed remote five-seed release run, including raw records and checksum,
is archived in [the remote core-benchmark report](docs/CORE_BENCHMARK_REMOTE_20260816.md).

## Related work

- Survey and broad benchmark context: [structural-entropy-survey-paper](https://github.com/SuuTTT/structural-entropy-survey-paper)
- NEST theoretical/audit manuscript: [nest-tcs-journal](https://github.com/SuuTTT/nest-tcs-journal)
- Paper B fair-comparison plan is maintained with the manuscript materials.

## License

MIT.
