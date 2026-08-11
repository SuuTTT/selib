# Claim-proof ledger

| Claim | Scope and quantifiers | Evidence | Proof or artifact | Forbidden stronger reading |
|---|---|---|---|---|
| Balanced two-module SE decision is NP-complete | Simple unweighted cubic graphs; balanced bipartitions; symbolic threshold | Exact affine identity and reduction from cubic Minimum Bisection | `sections/hardness.tex`; `results/tcs_balanced_se_bisection_check.json` | Does not prove unrestricted 2D-SE or full tree-SE is NP-hard |
| The edge-LCA graft change is exact | Every legal rooted graft on a weighted undirected graph with positive evaluated volumes | Subtraction of the edge-LCA expansion | Theorem 7; Appendix A.2 | Not an approximation ratio or runtime bound |
| The changed-incidence graft change is exact and path-supported | Same graft class; changed incidences defined by set difference | Cancellation of identical cluster-parent incidences | Theorem 8; `results/tcs_graft_reference_validation.json` | Does not imply the current reference code is asymptotically optimal |
| Every rooted NNI is a legal graft | Rooted binary trees under the paper's legality rules | Constructive mapping | Proposition 9 | Does not say every graft is one NNI |
| Exhaustive NEST-G termination certifies the declared neighborhood | Full legal graft enumeration, no round-cap termination, stated tolerance | Monotonicity, finiteness, final sweep | Propositions 11-12; tests | Does not certify global optimality |
| Two graft evaluators agree with full recomputation | 1,680 legal moves on 20 generated weighted graphs | Deterministic numerical validator | `results/tcs_graft_reference_validation.json` | Implementation agreement is not a proof of the theorem |
| Grafting repairs the five residual NEST misses | The five previously diagnosed exact-audit cases | Same graphs and restart streams; exact DP consulted after selection | `results/tcs_graft_exact_miss_diagnostic.json` | Does not estimate improvement frequency on unseen graphs |
| Rotation-only NEST wins the inherited 500-graph comparison | Five declared 64-vertex HSBM regimes and inherited protocol | Paired per-graph records and 95% CIs | `results/scale-audit-20260810/` | Does not establish superiority for arbitrary graph distributions |
| Rotation-only NEST reaches 370/375 inherited exact optima | Declared `n=12,14,16` suites and 32-start protocol | Independent subset DP | `results/scale-audit-20260810/` | Finite exact hits are not a worst-case guarantee |

## Pending claim

No population-level claim for NEST-G may enter the abstract, introduction, or
conclusion until `results/tcs_graft_confirmatory_exact12.json` contains all 100
records, matches the frozen source hashes, and passes the predeclared
falsifier in `results/tcs_graft_confirmatory_protocol.json`.
