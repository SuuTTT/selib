# SE--NNI artifact manifest

Frozen on 2026-08-10 for the NEST-only TAMC submission candidate.

## Source

- Repository: `https://github.com/SuuTTT/selib`
- Branch: `codex/se-hier-nni-paper`
- Evidence baseline commit: `ee545ff673908eed8e7df96cc3047a2f7621feb0`
- Restart repair and expanded audit: this manifest's containing commit
- Official HCSE/BBM comparison code commit: `ccf832e`
- Paper format: A4 Springer LNCS, 12 pages including references

## Exact artifact hashes (SHA-256)

| Artifact | SHA-256 |
|---|---|
| `paper/se-hier-nni/main.pdf` | `a81958c70459b6fb8f10a3e3af7af291ab58b3983fa396295c4e1cbef0244482` |
| `paper/se-hier-nni/main-with-appendix.pdf` | `d194678aa4cd24ce4dd0a164e7de79acc85dc51e4ad5552029f362606e95bae0` |
| `results/nni_benchmark.json` | `0fafdac19f3c70458b894027dffbdda67172861900812135bd4bb4673ba8345d` |
| `results/nni_real_benchmark.json` | `7c0c942455cf7b348935912068f0cb3d233b6e690c0a219ac8969e6e3e476d7d` |
| `results/nni_ablation.json` | `694fd324850573421862fb4697f0a14c28204f30df61cfff0497942cc2e3b71f` |
| `results/nni_optimality.json` | `ef6489bfe6392267b705150ae4668b9ab84c2bd69f5d34b3461a55da0d4f6dd6` |
| `results/nni_restart_audit.json` | `f62d825a13ba0092faf210722603c6578baf0c306476973f23f7fe40b57ee027` |
| `results/nni_restart_confirmation.json` | `aa198030cb7db20050037acbd4eb0ee95d18c51165f5e24af5be37658afbf77f` |
| `results/nni_restart_independent_confirmation.json` | `a9b470f7ef1f4cf9d132f47f059f77995ffc142f628b487e5faa3978b118feb1` |
| `results/nni_restart_failure_diagnostics.json` | `0a5a735d8630e6c21f265c3a95b4493115d25e2b6494714cff6257fd507cdc21` |
| `results/nni_restart_fairness.json` | `8e73c814bca695336d3bfff9a0aa73c2ca280212b51f6243375b70db5f973e07` |
| `results/nni_benchmark_repeat.json` | `0f67a2a89dbaed4570de88a4d7f30cbe5f2781ecb8e700eb8375ca9f88f75693` |
| `results/nni_basin_exact.json` | `d2a196aecba92355956bbbda4de03e7215e8802135f0965fa1acc7f651ca2bcb` |
| `results/nni_basin_monte_carlo.json` | `6db83cc29d8765c6287cb103eae0ab703c79d0f38e105749d1f628c297c34185` |

## Verification

- Main verifier: 350 unique paired records, 50 generator manifests, monotone NNI endpoints.
- Fair exact-optimum verifier: 250 fresh graphs, independent regime streams,
  and 32 candidates per restarted method. NEST is exact on 249/250, HCSE on
  2/250, and both BBM variants on 1/250; oracle BBM has 248 valid instances.
  The sole NEST gap is 0.07990%.
- Hard-case stochastic audit: R32 hit the optimum in 60/60 independent campaigns.
- Basin audit: all 146,580 rooted binary starts enumerated across one fixed
  noisy graph at each n=5--8; 80,000 direct starts over eight hard n=12 graphs;
  exact history-mass and frozen-count verifier passes.
- Tests: 19 passed, 1 skipped (`pytest -ra`).
- PDF: A4; 12-page main-plus-references artifact and 15-page combined artifact
  with three optional appendix pages; changed pages visually inspected after
  final compilation.
- TAMC double-blind checker: pass with zero mechanical failures; anonymous
  author and affiliation fields are required by the official review policy.

## Environment

- Exact-audit Python 3.12.13
- NetworkX 3.6.1
- NumPy 2.5.2
- SciPy 1.18.0
- scikit-learn 1.9.0
- pandas 3.0.5
- Matplotlib 3.11.1
- pdfTeX 1.40.29 / LaTeX2e 2025-11-01 / LNCS class 2.26

The frozen JSON files, rather than rounded table values, are the source of
truth. `scripts/make_nni_paper_artifacts.py` regenerates the main benchmark
tables and plots; the fair restart runner, candidate-level verifier, and report
generator regenerate and check the exact-audit table.
