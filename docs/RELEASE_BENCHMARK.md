# Core-release benchmark protocol

This is a compact **internal regression and comparability gate** for `selib`.
It is intentionally much smaller than the Paper B study.  Passing it means that
the native objectives, local-search implementations, and basic runtime reporting
remain reproducible; it does not establish a general SOTA claim.

## Conditions

| Block | Graphs | Methods | Purpose |
| --- | --- | --- | --- |
| Flat, topology-only | Karate; three 64-node fixed-seed SBMs | Louvain, spectral (`K` declared), `se_louvain`, fixed-`K` SE | inspect 2D-SE, ARI/NMI, module count, and wall time |
| Hierarchical audit | the same graphs | `optimal_tree`, `optimal_tree_nni`, `optimal_tree_nni_fast` | check monotonic tree entropy and report wall time |
| Exact verification | pytest small weighted graphs | DP, NNI, graft tests | compare local delta calculations with full re-scoring |

The three SBMs use `K=3` as a generator parameter.  Fixed-`K` SE and spectral
are labelled **known-K conditions** in the resulting JSON.  `se_louvain` does
not receive `K`; ARI/NMI are evaluator-only metrics.

## Command

```bash
python scripts/run_core_benchmark.py --seeds 0 1 2 3 4 \
  --output results/core_benchmark.json
```

The output stores raw per-seed records, host/Python metadata, and a summary.  A
published benchmark must use pinned environments, predeclared data splits,
resource limits, and the no-label protocol in the Paper B master plan.  Do not
quote the core-release file as a cross-paper leaderboard.
