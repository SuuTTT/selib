# Claim–proof ledger

| ID | Exact claim | Scope | Proof/evidence | Forbidden stronger reading | Status |
|---|---|---|---|---|---|
| C1 | The weighted rooted-NNI identity is the exact full-objective change. | Finite undirected nonnegative weighted graph; eligible positive-volume binary neighborhood. | Theorem 1; more than 100 random moves versus full rescoring at `1e-9`. | Does not imply every NNI improves. | proved |
| C2 | One-step descent is monotone and normally terminates at a one-NNI-local tree. | Eligible binary edges; excludes premature move-budget exhaustion. | Proposition 2; monotone traces and final-neighborhood tests. | Local is not global. | proved |
| C3 | Compound search never worsens its input and can escape a strict one-NNI trap. | Declared beam, barrier, and depth two. | Proposition 3; fixed `1.970038 -> 1.920593` witness. | It does not escape every trap. | proved |
| C4 | NEST returns the verified minimum among its successful refined candidates. | SE-agglomerative, recursive-SE, optional Paris, and any requested coalescent starts. | Selection code, per-candidate audit, unit tests. | It does not dominate every possible initializer. | proved |
| C5 | Every multiway encoding tree has a binary refinement of no greater entropy. | Nonnegative weighted graph. | Prior result: SuperTAD Lemma 3; also noted by HCSE. Our appendix re-derives the insertion delta `-2W(A,B) log(V_P/V_S)/vol(V)` for completeness. | Binary sufficiency is not our contribution; a particular arbitrary binary refinement need not be optimal. | prior / re-derived |
| C6 | The SE-specific arbitrary-subset trellis DP returns the global minimum over all encoding trees. | Positive-volume graph; exponential small-graph use. | DP recurrence plus prior C5; rebuilt optimum; enumeration of all 105 trees at n=5; generic trellis prior cited. | This is not a polynomial-time NEST guarantee, generic DP novelty, or SuperTAD's contiguity-constrained DP. | proved |
| C7 | NEST-R32 is exact on 800/800 audited n=12 graphs; standard NEST is exact on 685/800. | Five declared HSBM regimes and phased seeds; final 250 use disjoint regime streams. | Restart JSON artifacts and verifier; DP is exact. | No worst-case, size-independent, or all-graph optimality claim. | verified |
| C8 | NEST beats HCSE and BBM on the frozen external suite. | Five n=64 HSBM regimes, ten paired seeds. | `nni_benchmark.json`, verifier, paired CIs. | No universal dominance claim. | verified |
| C9 | On a fixed hard n=8 graph the exact coalescent basin mass is 0.252365; across eight hard n=12 graphs direct estimates range from 0.0807 to 0.4643. | One exhaustively enumerated noisy graph per n=5--8 and eight preidentified hard n=12 graphs with 10,000 starts each. | Basin JSON artifacts, exact history-mass identity, Clopper--Pearson intervals, and verifier. | No graph-independent success probability; 32 starts are not guaranteed. Strict planted recovery is a separate event and was not observed. | verified |

## Dependency graph

`structural-entropy definition` → `exact NNI delta` → local monotonicity and
compound safety → NEST; independently, `binary insertion delta` → binary
sufficiency → exact subset DP → finite global-optimum audit.

## Killed claims

- **General global optimality of NEST:** not proved; the standard pool misses
  audited instances, and finite random restarts carry no universal guarantee.
- **General approximation ratio:** not proved. All exact-hit rates and gaps are
  confined to the declared n=12 audit family.
- **Compound search always escapes:** false; beam, barrier, and depth are bounded.
- **Lower entropy always improves hierarchy labels:** unsupported; recovery is
  a separate metric.
- **NNI is newly invented:** false; novelty is the structural-entropy identity,
  certified optimizer, and global audit.
- **The 800/800 audit means NEST-R32 succeeds with probability one:** false;
  direct hard-case estimates include a 93.23% point estimate for 32 starts.
- **Reaching $H^*$ means recovering the planted hierarchy:** false on the
  declared small realized HSBMs under the strict all-clades criterion.

## Concurrent-work boundary

The Local-Traps/clique draft owns special unit-clique landscape analysis. This
paper owns arbitrary weighted-graph NNI optimization, the SE-specific
arbitrary-subset exact audit, NEST, and HSBM/real evidence. Binary sufficiency
is prior art. Do not submit essentially
overlapping manuscripts concurrently without chair guidance.
