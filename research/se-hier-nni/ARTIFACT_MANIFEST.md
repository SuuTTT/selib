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
| `paper/se-hier-nni/main.pdf` | `b57708dd55ac39e99614c0bbb648afbef59e9b5965636ffd1ec2388a3f99c574` |
| `paper/se-hier-nni/main-with-appendix.pdf` | `9048cdfba604bfbcf69106c5b15283866ef3731d8a564f11dbd1434c8667eb8e` |
| `output/pdf/NEST_TAMC2026_anonymous_with_appendix.pdf` | `9048cdfba604bfbcf69106c5b15283866ef3731d8a564f11dbd1434c8667eb8e` |
| `output/submission/NEST_TAMC2026_submission_package.zip` | `3355ce394ab53e65a429eb2e7ebe8a9aad3793837ee0bab51945e655254aa740` |
| `results/scale-audit-20260810/VERIFICATION_REPORT.json` | `0e33d3fba7cb7dbfdfa8c1a031cc1d1384058372aedf26386797c3359b0ea16d` |
| `results/scale-audit-20260810/n64-clean.json` | `7a639adac78ccb0c9301f7eaa126c72ca76987fc7bfe13e472fec57fb5541be1` |
| `results/scale-audit-20260810/n64-noisy.json` | `d3e2109f72ec7eb00fb210490e8d369a41fe00278ec33393b671e9f78d937851` |
| `results/scale-audit-20260810/n64-imbalanced.json` | `5a737ed260cbd1965fd581221fd8d87040ffbeda9b36290dbeaddd5e2baa261b` |
| `results/scale-audit-20260810/n64-weighted.json` | `c2f72f2d27577c82e50df498f6d239fef76d5544a9d6b60533796786f2a31f9a` |
| `results/scale-audit-20260810/n64-weak.json` | `e302c8071dfc2c3d334bbe71a5a5adb255d63ec6f6b447ee8db7e40b2dc87cc6` |
| `results/scale-audit-20260810/exact14.json` | `db9680034a2be3c944c7d464d8d3594407eabda4380ff5b4d8b88984f0892162` |
| `results/scale-audit-20260810/exact16.json` | `0942421dec5e4cc03a8ba6843009ab2655cd203b2fd5d0d99c94f1c2bac7b45f` |
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

- Scaled main verifier: 3,500 unique method records, 500 generator manifests,
  complete seeds 1000--1099 in each regime, matching SHA-256 seals, finite
  metrics, and monotone NNI endpoints. NEST wins 500/500 paired comparisons
  against the better of HCSE and BBM by 0.4239 +/- 0.0086 bits.
- Fair exact-optimum verifier: 375 sealed graphs across n=12, 14, and 16 with
  independent regime streams and 32 candidates per restarted method. NEST is
  exact on 370/375, HCSE on 2/375, and label-free BBM on 1/375. The completed
  n=14 and n=16 blocks have matching status and hash seals; the interrupted
  1,000-instance exact12 checkpoint is excluded.
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
truth. `scripts/verify_nni_scale_audit.py` validates the scaled evidence, and
`scripts/make_nni_scale_submission_artifacts.py` regenerates its tables and
plots. The fair restart runner and candidate-level verifier regenerate and
check the exact-audit records.
