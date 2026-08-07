# Claim–proof ledger

| ID | Exact claim | Scope/quantifiers | Closest prior theorem | Exact novelty delta | Proof location | Finite certificate/test | Forbidden stronger reading | Independent review | Status |
|---|---|---|---|---|---|---|---|---|---|
| C1 | Eq. (3) is the exact change in full tree structural entropy for `((A,B),C) -> (A,(B,C))`. | Every finite undirected nonnegative weighted graph with positive total volume; eligible rooted binary neighborhood. | Jowhari 2024 derives local-search behavior for a different linear/revenue HC objective; the concurrent clique-landscape draft contains the unit-clique specialization. | Weighted graph cuts and volumes for the complete SE objective; explicit indispensable parent-volume term. | Theorem 1 and its direct boundary-cancellation proof. | `test_weighted_nni_delta_matches_full_entropy_recomputation`: >100 random weighted moves, tolerance `1e-9`. | Does not imply the move is improving, or that NNI finds the global optimum. | A separate independent proof read is still required before upload. | proved; review open |
| C2 | Exact one-step descent never worsens the input and, on normal budget termination, returns a one-NNI-local tree over every eligible binary edge. | Same graph/tree scope as C1; tolerance `1e-10`; excludes premature move-budget exhaustion. | Standard finite local-search reasoning; Jowhari 2024 for a different objective. | A checkable certificate under the actual structural-entropy delta. | Proposition 1. | Monotonic trace and final-neighborhood regression tests. | “NNI-local” is not “globally optimal.” | Automated tests only. | proved; review open |
| C3 | Bounded compound search never worsens its input and may improve a strict one-NNI local optimum. | Beam/barrier-limited two-step search; endpoint accepted only after exact recomputation. | Concurrent clique-landscape draft studies a special analytic two-NNI escape. | Implemented arbitrary-weight graph search with a safe endpoint rule and regression witness. | Proposition 2. | Fixed eight-node witness: `1.970038 -> 1.920593` bits; positive first barrier. | Does not guarantee escape from every NNI trap or completeness of depth-two search outside the beam. | Automated test only. | proved; review open |
| C4 | `SE-NNI-fast` is no worse than its NNI-refined candidate starts and returns the verified minimum among successful SE-agglomerative, recursive-SE, and Paris starts. | Successful constructors only; Paris optional and recorded. | Multi-start construction is used broadly; no checked prior combines this pool with exact SE-NNI certification. | Auditable initializer selection plus exact objective verification. | Method Sec. 4.3 and implementation `encoding_tree_nni_fast`. | Unit test shows no worse than the SE-agglomerative start; per-run candidate entropy audit. | Not guaranteed no worse than the slow released `se_hier`; the compatibility variant is. | Automated tests only. | proved; review open |
| C5 | NNI exposes a reproducible local-optimality gap in established constructors. | Five frozen HSBM regimes, ten paired seeds, named methods. | HCSE/BBM/Paris papers report constructor quality, not this audit. | Per-constructor one-NNI and compound gap rates under one evaluator. | Experiment Tables 1--3 and Fig. 3. | `verify_nni_benchmark.py`; 350 raw records and 50 manifests. | No claim outside tested graphs; no claim that lower entropy always improves labels. | Automated cross-artifact review complete; external read recommended. | verified |
| C6 | `SE-NNI-fast` improves the entropy--runtime frontier relative to released `se_hier`. | Frozen HSBM suite, four real networks, and timing-only size sweep on declared hardware/software. | Released SELib implementation. | Replaces expensive generic edits with exact local rotations and bounded compound search. | Experiment Figs. 2--3 and real/scaling tables. | `verify_nni_supplements.py`; paired H/time records and scaling JSON. | No asymptotic speedup theorem; no hardware-independent constant factor. | Automated cross-artifact review complete; external read recommended. | verified |

## Dependency graph

`tree structural-entropy definition` → `boundary union identity` → **C1 exact delta** →
**C2 monotone descent/local certificate** → **C3 safe compound endpoint** →
**C4 fast multi-start selection** → paired experimental claims **C5–C6**.

The empirical claims depend on the theorem-backed implementation and frozen evaluator, but
the proofs do not depend on benchmark outcomes.

## Killed claims

- **Global optimality:** killed by known NNI-local nonglobal trees; banned everywhere.
- **Fast variant is always no worse than released `se_hier`:** not guaranteed because the fast
  method intentionally omits generic collapse/relocation. Only identical-start monotonicity and
  candidate-pool dominance are permitted.
- **Compound search always escapes:** false; it is bounded by beam, barrier, and depth two.
- **Every constructor is NNI-improvable:** false for multiway/two-level outputs with no eligible
  binary neighborhoods and for already local trees.
- **Lower `H^T` always improves hierarchy recovery:** unsupported; purity is a separate metric.
- **SE-NNI beats every baseline on every graph:** contradicted by development and early frozen
  runs where oracle-`k` BBM or Paris has lower entropy.
- **The parent-volume term cancels:** false in general. Equation (4) retains
  `(W(A,B)-W(B,C)) log V_P` explicitly.

## Concurrent-work ownership

| Work | Imported/shared material | Owned by this paper | Required action |
|---|---|---|---|
| Clique/curvature/Local-Traps manuscript | Rooted NNI definition, unit-clique specialization, special analytic local traps and barriers. | Arbitrary weighted-graph optimizer, full-objective verification, fast multi-start method, implementation, HSBM/real/scaling evidence. | Do not submit overlapping manuscripts concurrently unless chairs confirm separation; disclose the related manuscript and never reclaim its special-family theorems. |
| Released SELib | `se_hier`, SE agglomeration, recursive-SE, evaluator, Paris adapter. | New NNI functions, compound search, fast public API, tests, benchmark and manuscript. | Cite/version the software and distinguish prior released functionality from additions on this branch. |

## Independent-review blocker

Before EasyChair upload, an external human read should check Theorem 1's algebra,
the scope of Propositions 1--2, the concurrent-paper boundary, and the final claim wording.
The internal gate already includes a second expanded derivation, random weighted
full-objective checks, endpoint verification, and a literature novelty audit.
