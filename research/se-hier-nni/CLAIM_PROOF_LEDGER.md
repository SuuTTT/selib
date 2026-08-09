# Claim–proof ledger

| ID | Exact claim | Scope | Proof/evidence | Forbidden stronger reading | Status |
|---|---|---|---|---|---|
| C1 | The weighted rooted-NNI identity is the exact full-objective change. | Finite undirected nonnegative weighted graph; eligible positive-volume binary neighborhood. | Theorem 1; more than 100 random moves versus full rescoring at `1e-9`. | Does not imply every NNI improves. | proved |
| C2 | One-step descent is monotone and normally terminates at a one-NNI-local tree. | Eligible binary edges; excludes premature move-budget exhaustion. | Proposition 2; monotone traces and final-neighborhood tests. | Local is not global. | proved |
| C3 | Compound search never worsens its input and can escape a strict one-NNI trap. | Declared beam, barrier, and depth two. | Proposition 3; fixed `1.970038 -> 1.920593` witness. | It does not escape every trap. | proved |
| C4 | NEST returns the verified minimum among its successful refined candidates. | SE-agglomerative, recursive-SE, and optional Paris starts. | Selection code, per-candidate audit, unit tests. | It does not dominate every possible initializer. | proved |
| C5 | Every multiway encoding tree has a binary refinement of no greater entropy. | Nonnegative weighted graph. | Binary-sufficiency proposition; insertion delta `-2W(A,B) log(V_P/V_S)/vol(V)`. | A particular arbitrary binary refinement need not be optimal. | proved |
| C6 | The subset DP returns the global minimum over all encoding trees. | Positive-volume graph; exponential small-graph use. | DP recurrence plus C5; rebuilt optimum; independent enumeration of all 105 trees at n=5. | This is not a polynomial-time NEST guarantee. | proved |
| C7 | NEST is exact on 45/50 audited n=12 graphs and within 3.72% on all 50. | Five frozen HSBM regimes, ten seeds, n=12. | `nni_optimality.json` and verifier; DP is exact. | No worst-case or size-independent approximation ratio. | verified |
| C8 | NEST beats HCSE and BBM on the frozen external suite. | Five n=64 HSBM regimes, ten paired seeds. | `nni_benchmark.json`, verifier, paired CIs. | No universal dominance claim. | verified |

## Dependency graph

`structural-entropy definition` → `exact NNI delta` → local monotonicity and
compound safety → NEST; independently, `binary insertion delta` → binary
sufficiency → exact subset DP → finite global-optimum audit.

## Killed claims

- **General global optimality of NEST:** false; five exact-suite instances are
  nonglobal.
- **General approximation ratio:** not proved. The 3.72% number is confined to
  the declared 50 exact-solvable graphs.
- **Compound search always escapes:** false; beam, barrier, and depth are bounded.
- **Lower entropy always improves hierarchy labels:** unsupported; recovery is
  a separate metric.
- **NNI is newly invented:** false; novelty is the structural-entropy identity,
  certified optimizer, and global audit.

## Concurrent-work boundary

The Local-Traps/clique draft owns special unit-clique landscape analysis. This
paper owns arbitrary weighted-graph NNI optimization, binary sufficiency, the
exact subset audit, NEST, and HSBM/real evidence. Do not submit essentially
overlapping manuscripts concurrently without chair guidance.
