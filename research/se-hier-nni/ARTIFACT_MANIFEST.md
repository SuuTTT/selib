# SE--NNI artifact manifest

Frozen on 2026-08-08 for the TAMC submission candidate.

## Source

- Repository: `https://github.com/SuuTTT/selib`
- Branch: `codex/se-hier-nni-paper`
- Evidence-and-paper commit: `89bc9514931a1fe56415f0c57e4dd8f09ac440fa`
- Official HCSE/BBM comparison code commit: `ccf832e`
- Paper format: A4 Springer LNCS, 11 pages including references

## Exact artifact hashes (SHA-256)

| Artifact | SHA-256 |
|---|---|
| `paper/se-hier-nni/main.pdf` | `d19aa4095ecb5353fac354e21c19c486c2b26a998ff5098be40603ebe4ccbe94` |
| `results/nni_benchmark.json` | `0fafdac19f3c70458b894027dffbdda67172861900812135bd4bb4673ba8345d` |
| `results/nni_real_benchmark.json` | `7c0c942455cf7b348935912068f0cb3d233b6e690c0a219ac8969e6e3e476d7d` |
| `results/nni_scaling.json` | `930d73412a07bee34528fa3cb6b40f50172a7d42c911f3df76fd8ad9341f74ad` |
| `results/nni_ablation.json` | `694fd324850573421862fb4697f0a14c28204f30df61cfff0497942cc2e3b71f` |
| `results/nni_benchmark_repeat.json` | `0f67a2a89dbaed4570de88a4d7f30cbe5f2781ecb8e700eb8375ca9f88f75693` |

## Verification

- Main verifier: 350 unique paired records, 50 generator manifests, monotone NNI endpoints.
- Supplement verifier: 28 real-network records, 24 scaling records, 250 ablation records, and 50 exact cross-artifact matches.
- Tests: 10 passed, 1 skipped (`.venv/bin/pytest -q`).
- PDF: A4, 11 pages, all fonts embedded, no Type 3 fonts; visually inspected after final compilation.
- TAMC double-blind checker: pass with zero mechanical failures; anonymous
  author and affiliation fields are required by the official review policy.

## Environment

- Python 3.14.6
- NetworkX 3.6.1
- NumPy 2.5.1
- SciPy 1.18.0
- scikit-learn 1.9.0
- pandas 3.0.5
- Matplotlib 3.11.1
- pdfTeX 1.40.29 / LaTeX2e 2025-11-01 / LNCS class 2.26

The frozen JSON files, rather than rounded table values, are the source of
truth. `scripts/make_nni_paper_artifacts.py` regenerates every reported table,
macro, and plot from those artifacts.
