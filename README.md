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

## Gap audit (2026-09-02) — what is solved, what is open, before the world-model project

Audit of [issue #10](https://github.com/SuuTTT/selib/issues/10) (six gaps between SE and world
models), [issue #12](https://github.com/SuuTTT/selib/issues/12), the six follow-up research
packages, and `main` at `68ab285`. "Verified" = the package's own self-test / fixture or a
reproduction script was run on 2026-09-02 (Python 3.14, numpy 2.5, networkx 3.6).

### Gaps from issue #10

| # | Gap | Status | Where | Verified 2026-09-02 |
|---|---|---|---|---|
| G1 | Tree depth unidentifiable (SE indifferent to binary refinement) | **Solved in package.** MDL tree cost `L = vol·H^T + U + C`; exact collapse condition; depth recovered exactly at d = 1–3, resolution limit at d = 4. Prop 3: degree-matched nulls always keep one spurious level, so depth must be reported null-calibrated. | `SuuTTT/se-depth-mdl` (private) | `code/mdl_tree.py` selftests: ALL PASSED |
| G2 | No null model in the definition | **Solved in package.** Closed-form `E_null[H]` (exact linearity in the cut vector; exact configuration-model moments); calibrated SE = code-length-weighted modularity under Chung–Lu; `se_report()` with null mean / CI / gap / z / hashes. Boundary: fixed-partition calibration does **not** remove partition-optimization bias — cross-graph comparisons need the sampled *optimized* null. Label-tracking gate G4b FAILED (calibration ≠ margin). | `SuuTTT/se-null-calibration` (private) | `gap2_smoke.py`: ALL SMOKE TESTS PASSED, incl. `se_report` end-to-end |
| G3 | Undirected only; self-loops undefined | **Solved in package.** Flow-based directed 2D/tree SE with exact reduction to Li–Pan on undirected graphs; jump/dwell self-loop convention; directed degree-preserving null; flow-Louvain; in-repo map equation for Infomap positioning. 15/15 SE-JEPA latent graphs (79–91 % self-loop mass) give coherent modules under the jump convention. | `SuuTTT/se-directed` (private) | `code/test_dirse.py`: ALL PASS |
| G4 | Requires a discrete graph | **Partially solved.** Theory of the soft relaxation: the deployed bilinear objective (`selib.segnn.soft_se2d`, DeSE, LSEnet, DMoN-style) is **provably loose**; the multilinear extension is exact; bits-back identity links them. Two gates FAILED verbatim; the `H_code ≥ H_mul ≥ H_bil` sandwich is a conjecture. The latent → graph discretisation confound for world models remains an experimental issue. | `SuuTTT/se-soft` (private) | `code/selftest.py`: ALL PASS |
| G5 | No timescale semantics | **Solved in package.** SE spectrum of `P^k` with a margin-preserving flow null; exact persistence identity; knees at `k ~ 1/(1−λ)`; metastable partition unique iff block volumes < ½ (sharp). Gates G1/G2/G2b/G3 PASS 5/5. On SE-JEPA latents stride 1 is **not** significant; the spectrum peaks at `k* = 11–16`; the partition path coarsens smoothly (a continuum of scales, no plateau). | `SuuTTT/se-spectrum` (private) | `fixtures/multiscale_fixture.py`: FIXTURE PASS (9 s) |
| G6 | Disconnected from control | **Half solved.** Blindness theorem: passive SE cannot see control. Control gain `dH_ctrl = I(A; m(S′) | m(S))` tracks a controllability knob at ρ = 0.981, calibrated. The quotient-planning gate **FAILED**: neither control-aware nor plain-SE nor an ideal partition preserved plans — reward-awareness appears necessary for plan-preserving abstraction. | `SuuTTT/se-control` (private) | `fixtures/fixture_control.py`: FIXTURE PASS |

### Gaps from issue #12 and integration gaps on `main`

| # | Gap | Status | Where | Verified |
|---|---|---|---|---|
| B1 | `se_optimize(G, k=K)` silently returns fewer than `K` communities when `K` exceeds its natural optimum | **Open bug.** | `selib/seopt.py` (`_merge_down_to_k` cannot split) | Reproduced on `main`: `ring_of_cliques(4,6)`, `k=9` → 4 communities, **0 warnings** |
| B2 | Comparing SE with resolution-parameterised baselines at self-selected `k` confounds criterion with resolution (retracted a world-model result) | **Open.** No matched-`k` sweep helper in `selib.benchmark`. | `selib/benchmark.py` | grep: none |
| I1 | None of the six packages is merged; `se_report()` on `main` reports no null; the validation fixtures live only in the private repos | **Open.** | `selib/calc.py`, PRs #7–#11 only | `pytest`: 24 passed, 1 skipped on `main` |
| I2 | `python selib/calc.py` fails (relative import) when run as a script; the selftest only works via `python -m` | Minor | `selib/calc.py` | Reproduced |

### New gaps found while preparing the world-model project (toy scale, uncalibrated)

| # | Gap | Status |
|---|---|---|
| N1 | **Size dominance at stride 1.** The entering term is O(cut/vol) (≈ 0.003 bits for a one-edge door) while the locating term is O(1) and shrinks with community size, so 2D SE prefers ~12-node patches to 4 rooms on a lattice (5.61 vs 4.32 bits); Infomap agrees. Going one tree level deeper gains ~0.001 bits. | Explained; **mitigated by G5**: at Markov time k ≈ 16 rooms overtake patches and the optimizer's partition aligns with rooms at NMI 0.82 — but settles on half-rooms, consistent with G5's "continuum of scales". |
| N2 | **Task-flow (betweenness) edge reweighting makes it worse** (31 communities; heavily used doors get merged across). Flow-coding objectives find traps, not highways. | Negative result, recorded. Task-conditioning must enter via horizon (→ Markov time) or a reference partition, not edge weights. Consistent with G6's blindness theorem. |
| N3 | **SE of a partially observed graph is biased**: a half-revealed lattice is tree-like and *more* compressible than the full one, so "reduction in SE" used as a learning-progress reward is sign-confounded during exploration. No theory for SE under missing edges / online smoothing (cf. survey O2, incremental SE). | **Open.** Progress must be defined on a fixed state set with a smoothed transition estimate. |
| N4 | **Structural progress as an exploration reward** has no theory, and its noise-robustness is already owned by learning-progress methods (LPM, 2025). Novelty can only be organization-vs-predictability, untested. | **Open.** |
| N5 | **Encoding-tree waypoints / boundary criteria for hierarchical world models** (the paused paper's use) require G5 + B2 + G2 first. | **Open**, prerequisites now exist. |
| N6 | All toy δ values above are **uncalibrated** (no degree-matched null). | **Action:** rerun through `se-null-calibration`'s `se_report` before quoting any of them. |

### Before starting the world-model project — checklist

1. Latent transition graphs: use the **directed jump/dwell convention** (G3) and the **flow-margin null** (G5); never symmetrise and never keep naive self-loops.
2. Never report δ or H without `E_null` (G2). Cross-graph comparisons need the *optimized* null.
3. Never compare SE against modularity/Infomap at self-selected `k`; sweep `k` for every method (B2).
4. After any `se_optimize(G, k=K)`, check `len(set(labels)) == K` (B1).
5. Depth claims only via the MDL tree cost with null-calibrated depth (G1); pure-SE depth is not identifiable.
6. Soft objectives: report the bilinear value against its floor, or use the multilinear extension (G4).
7. Any planning/control claim needs a **reward-aware arm**; reward-free SE quotients failed the planning gate (G6).
8. Time scale first: compute the SE spectrum and work at its significant `k` range; stride-1 results on latents evaporate (G5).
9. Exploration-progress rewards: fixed state set + smoothed transitions (N3); baselines must include LPM/VIME (N4).
10. Preregister gates (`GATE.md` pattern of the six packages) and report failures verbatim.
