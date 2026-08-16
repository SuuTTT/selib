# Remote core-benchmark result — 2026-08-16

This is the completed five-seed execution of the compact release protocol in
[`RELEASE_BENCHMARK.md`](RELEASE_BENCHMARK.md), run from `selib` `main` after
the audited NEST core release.  The raw seed-level records are in
[`../results/core_benchmark_remote_5seed_20260816.json`](../results/core_benchmark_remote_5seed_20260816.json).

## Execution envelope

- Existing Vast.ai instance; no instance was rented, started, stopped, or
  restarted for this run.
- CPU only; no GPU was used by the benchmark.
- Four CPU cores, `nice -n 19`, and a temporary directory because the remote
  workspace was not backed by a persistent volume.
- Five seeds (`0` through `4`); 130 raw records; total measured algorithm time
  195.598 seconds.
- SHA-256 of the raw JSON:
  `053ae45424b00b4aaa1cca2a5a4881d94a61538587e63c67b882ae31a0849d42`.

## Hierarchical result

Values are mean tree structural entropy $H^T$ (bits) / mean wall-clock seconds.
Lower is better for both columns independently; this table is a compact native
regression check, not a cross-paper leaderboard.

| Dataset | `se_hier` | `se_hier_nni` | `se_nni_fast` |
| --- | ---: | ---: | ---: |
| Karate | 2.5217 / 0.9408 | 2.5145 / 0.9644 | **2.4605 / 0.1239** |
| SBM-Clean | 3.8185 / 5.9412 | 3.8086 / 6.0500 | **3.6865 / 0.3136** |
| SBM-Moderate | 3.7732 / 6.1585 | 3.7477 / 6.2020 | **3.7414 / 0.2809** |
| SBM-Noisy | 3.8343 / 5.7701 | 3.8107 / 5.8527 | **3.8107 / 0.2147** |

`se_nni_fast` is no worse in the recorded tree objective on all four release
graphs and is substantially faster than the generic hierarchy refinement.  The
flat results in the raw file are intentionally kept separate: known-`K`
baselines are labelled as such, and ARI/NMI are evaluation-only for free-`K`
methods.

## Reproduce

```bash
python scripts/run_core_benchmark.py --seeds 0 1 2 3 4 \
  --output results/core_benchmark.json
sha256sum results/core_benchmark.json
```

Hardware and package versions vary, so wall-clock values should be treated as
release-environment observations rather than portable performance guarantees.
