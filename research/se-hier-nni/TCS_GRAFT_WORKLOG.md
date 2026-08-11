# TCS Graft Worklog

## 2026-08-11: correctness-first rooted subtree graft

### Operator

For a rooted binary encoding tree, choose a non-root source subtree `S` and a
target subtree `Q` that is neither an ancestor nor a descendant of `S`. Detach
`S`, suppress its now-unary parent, and replace `Q` by a new binary parent with
children `S,Q`. Same-parent pairs are omitted because they recreate the same
unordered hierarchy.

The reference search enumerates all legal ordered source--target pairs, fully
recomputes tree structural entropy, commits only the best strict decrease, and
runs exact NNI descent after every accepted graft. If a sweep finds no strict
decrease, the endpoint is locally optimal for the declared exhaustive graft
neighborhood and one-NNI-local when post-graft NNI is enabled.

### Exact edge--LCA delta

The edge--LCA expansion is

```text
H^T(G) = sum_{uv in E} (w_uv/M)
         log_2(V_lca_T(u,v)^2 / (d_u d_v)),
```

where `M=vol(G)`. Hence for any legal graft taking `T` to `T'`,

```text
H^{T'}(G)-H^T(G)
  = (2/M) sum_{uv in E} w_uv
      log_2(V_lca_T'(u,v) / V_lca_T(u,v)).
```

The degree terms cancel. Modules outside the removal and insertion ancestor
paths retain both their leaf sets and volumes, so their edge--LCA buckets
cancel. The current correctness implementation scans all sparse edges and lets
unchanged terms evaluate to zero. The optimized implementation will cache edge
weight by LCA module and visit only affected path buckets.

An initially tempting stronger shortcut was false: it is not enough to sum
only edges crossing `S`. Ancestor modules on the insertion path gain `S`, and
ancestor modules on the removal path lose `S`; therefore an edge with neither
endpoint in `S` can change contribution when its LCA is one of those modules.
The deterministic validator found this immediately. On its first counterexample
the cut-edge-only prediction was `-0.1196107795` bits while the true change was
`+0.1065208696` bits. This failed shortcut must not appear in the paper.

### Reference validation

Run:

```bash
.venv/bin/python scripts/validate_graft_reference.py
```

The deterministic suite checks:

- 1,680 legal grafts across 20 weighted graph/tree cases;
- preservation of a rooted binary topology and exactly one copy of every leaf;
- exact edge--LCA delta versus complete structural-entropy recomputation;
- monotone best-improvement refinement on four independent cases; and
- exhaustive absence of an improving graft at every returned endpoint.

The maximum delta discrepancy was `1.4016565685892601e-15` bits. Artifact:
`results/tcs_graft_reference_validation.json`.

### Five sealed misses

Run:

```bash
.venv/bin/python scripts/diagnose_exact_misses_with_graft.py
```

The script reconstructs the exact graph and restart streams declared by the
frozen n=12, n=14, and n=16 audits. It applies the richer optimizer to every
one of the same 32 random-coalescent candidates, selects by structural entropy,
and consults the exact optimum only afterward.

| n | Regime / seed | Frozen gap (bits) | After graft | Restarts improved |
|---:|---|---:|---:|---:|
| 12 | clean / 168 | 0.001323320 | exact | 31/32 |
| 14 | weak hierarchy / 3004 | 0.002439840 | exact | 18/32 |
| 16 | noisy / 4001 | 0.005273867 | exact | 23/32 |
| 16 | noisy / 4002 | 0.007208013 | exact | 28/32 |
| 16 | weak hierarchy / 4002 | 0.010305078 | exact | 26/32 |

Thus exhaustive graft refinement closes all five preidentified failures. This
is mechanism discovery, not an unbiased estimate of future exact-hit rate. The
method must now be frozen and evaluated on newly generated sealed instances.
Artifact: `results/tcs_graft_exact_miss_diagnostic.json`.

### Next proof and algorithm tasks

1. Prove the exact characterization of affected old/new LCA buckets on the two
   ancestor paths.
2. Implement a cached path scorer and check every predicted delta against the
   full-rescore reference within `1e-9`.
3. Prove that one NNI is a special case of a graft and bound the number of NNIs
   needed to realize a general graft as a function of source--target distance.
4. Freeze NNI-plus-graft before a new matched, sealed evaluation.
5. Construct strict-separation families where NNI-local trees admit an
   improving graft, then quantify the intervening NNI barrier.
