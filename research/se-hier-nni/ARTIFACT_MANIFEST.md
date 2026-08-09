# SE--NNI artifact manifest

Frozen on 2026-08-10 for the NEST-only TAMC submission candidate.

## Source

- Repository: `https://github.com/SuuTTT/selib`
- Branch: `codex/se-hier-nni-paper`
- Evidence-and-paper commit: `ee545ff673908eed8e7df96cc3047a2f7621feb0`
- Official HCSE/BBM comparison code commit: `ccf832e`
- Paper format: A4 Springer LNCS, 12 pages including references

## Exact artifact hashes (SHA-256)

| Artifact | SHA-256 |
|---|---|
| `paper/se-hier-nni/main.pdf` | `41b2ad17b4bfeca03910e04a56f1473fad561c66bf78d241f5617066e70653e1` |
| `results/nni_benchmark.json` | `0fafdac19f3c70458b894027dffbdda67172861900812135bd4bb4673ba8345d` |
| `results/nni_real_benchmark.json` | `7c0c942455cf7b348935912068f0cb3d233b6e690c0a219ac8969e6e3e476d7d` |
| `results/nni_ablation.json` | `694fd324850573421862fb4697f0a14c28204f30df61cfff0497942cc2e3b71f` |
| `results/nni_optimality.json` | `ef6489bfe6392267b705150ae4668b9ab84c2bd69f5d34b3461a55da0d4f6dd6` |
| `results/nni_benchmark_repeat.json` | `0f67a2a89dbaed4570de88a4d7f30cbe5f2781ecb8e700eb8375ca9f88f75693` |

## Verification

- Main verifier: 350 unique paired records, 50 generator manifests, monotone NNI endpoints.
- Exact-optimum verifier: 50 unique n=12 records, 45 exact NEST optima,
  0.1181% mean relative gap, and 3.7155% maximum relative gap.
- Tests: 14 passed, 1 skipped (`pytest -q`).
- PDF: A4, 12 pages, all fonts embedded, no Type 3 fonts; visually inspected after final compilation.
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
truth. `scripts/make_nni_paper_artifacts.py` regenerates every reported table,
macro, and plot from those artifacts.
