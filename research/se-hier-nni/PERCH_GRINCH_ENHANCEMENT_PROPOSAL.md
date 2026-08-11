# Proposal: Entropy-Certified Grafting Beyond Local NNI

**Working method name:** NEST-G (NEST with certified graft search)

**Status:** proposal; do not change the submitted TAMC paper until the Phase-1 gate passes

**Submitted reference state:** local annotated tag `tamc2026-submitted`, commit `7e93199`

**Primary objective:** full tree structural entropy \(H^T(G)\), in bits; lower is better

## TL;DR

NEST repairs a hierarchy by rotating one nearby tree edge at a time. PERCH uses
the same kind of local child--aunt swap while data arrive, and GRINCH adds a
larger operation that cuts a whole subtree from one location and attaches it
near a distant subtree. The promising extension is **not** to copy their
distance or linkage rules. It is to borrow the larger graft move, calculate its
effect on structural entropy exactly, and accept it only when the complete
tree becomes better.

The first decisive test is small and cheap: NEST misses the known global
optimum on only five of the current 375 exact-audit graphs. If an exact graft
repairs at least four of these five cases, especially the three \(n=16\) cases,
the extension is worth developing. If it repairs none, it should remain a
related-work discussion rather than enlarge the paper.

## 1. What PERCH and GRINCH actually contribute

### PERCH

PERCH is an online hierarchical clustering algorithm for Euclidean point data.
It inserts a new point next to its nearest existing leaf, then swaps a child
with its aunt when a masking test detects a likely purity error. It also uses
balance-improving swaps to keep the tree shallow and bounding boxes to speed
nearest-neighbor and masking tests.

The child--aunt swap is topologically a rooted NNI. The important differences
from NEST are:

- PERCH inspects a restricted path associated with the newly inserted point;
- its move test is based on pairwise distance bounds and tree balance;
- its theorem proves perfect dendrogram purity under strict Euclidean
  separability; and
- it does not minimize or certify structural entropy.

PERCH is therefore useful as prior art for **online rotations, balance, and
fast candidate routing**, but its published move condition cannot replace the
exact NEST delta.

### GRINCH

GRINCH generalizes the online setting to arbitrary set-level linkage functions.
After insertion and local rotations, it performs a nonlocal graft: a subtree
\(S\) searches for a distant subtree \(Q\), and they are joined when each
prefers the other to its current sibling under linkage \(f\). A restructuring
pass repairs the path disturbed by a successful graft.

Its theorem is also different from NEST's target. Under model-based separation,
GRINCH recovers a tree containing the ground-truth connected components,
independent of arrival order. It does not show that a graft lowers structural
entropy. Its experiments also reveal an instructive effect: the immediate
dendrogram-purity change of a graft can be tiny, while the corrected tree makes
later insertions substantially better. This makes grafting compelling for
online construction, but it does not establish an offline SE improvement.

### Relationship to NEST

| Property | PERCH | GRINCH | Submitted NEST | Proposed NEST-G |
|---|---|---|---|---|
| Setting | online Euclidean points | online, general linkage | offline weighted graph | offline weighted graph first; online later |
| Local move | child--aunt rotation | child--aunt rotation | exhaustive rooted NNI | rooted NNI |
| Nonlocal move | none | subtree graft + restructure | bounded two-NNI path | subtree prune-and-regraft |
| Move score | masking/balance | linkage preference | exact \(\Delta H^T\) | exact \(\Delta H^T\) |
| Acceptance | heuristic condition | heuristic condition | verified lower endpoint | verified lower endpoint |
| Certificate | purity under separability | recovery under model separation | one-NNI local optimum | NNI + declared graft-neighborhood optimum |

## 2. Research gap

The submitted NEST search is strong but local. One NNI changes one internal
edge, and the bounded two-move stage crosses only a shallow, two-edge barrier.
The exact audit shows five residual misses:

| \(n\) | Regime | Graph seed | NEST gap (bits) | Relative gap |
|---:|---|---:|---:|---:|
| 12 | clean | 168 | 0.00132332 | 0.07990% |
| 14 | weak hierarchy | 3004 | 0.00243984 | 0.12060% |
| 16 | noisy | 4001 | 0.00527387 | 0.23193% |
| 16 | noisy | 4002 | 0.00720801 | 0.31627% |
| 16 | weak hierarchy | 4002 | 0.01030508 | 0.44934% |

These cases are the right diagnostic because their global optima are already
known and hidden from candidate selection. The central question is:

> Are the remaining errors caused by NEST's local move radius, and can a
> nonlocal subtree graft close them while preserving exact objective control?

No checked PERCH/GRINCH result answers this question: their move rules optimize
distance/linkage surrogates and their guarantees concern planted-cluster
recovery rather than weighted graph structural entropy.

## 3. Proposed method

### 3.1 Faithful SE setting

- \(G=(V,E,w)\) is the same fixed, undirected, nonnegative weighted graph used
  by NEST.
- \(2m=\sum_{v\in V}d_v\) is total graph volume.
- A leaf of \(T\) is one vertex; an internal node is a vertex module.
- \(V_\alpha=\sum_{v\in\alpha}d_v\) and \(g_\alpha\) is the weighted cut of
  module \(\alpha\).
- Every candidate is scored by the full tree objective

  \[
  H^T(G)=-\sum_{\alpha\ne\lambda}
  \frac{g_\alpha}{2m}\log_2\frac{V_\alpha}{V_{\alpha^-}}.
  \]

- No ground-truth label, exact optimum, or planted hierarchy is used to propose
  or select a move.

### 3.2 Entropy-certified subtree graft

Choose a non-root subtree \(S\) and a target subtree \(Q\) that is neither an
ancestor nor a descendant of \(S\). Detach \(S\), suppress the resulting unary
node, insert a new binary parent for \(S\) and \(Q\), and update the two paths
to their old least common ancestor. This is a rooted subtree
prune-and-regraft move, analogous to GRINCH's nonlocal correction but applied
offline to an existing encoding tree.

The safe reference implementation will:

1. clone the current tree;
2. apply one legal graft;
3. recompute all module volumes, cuts, and \(H^T\);
4. accept only a strictly lower endpoint; and
5. rerun exact one-NNI descent after every accepted graft.

This version is slower but establishes correctness before optimization.

### 3.3 Exact path delta

A graft changes only the new \(S\cup Q\) module and modules on the removal and
insertion paths up to their old LCA. For a module \(U\) on the insertion path,

\[
V_{U\cup S}=V_U+V_S,\qquad
g_{U\cup S}=g_U+g_S-2W(S,U).
\]

For a module \(U\supset S\) on the removal path,

\[
V_{U\setminus S}=V_U-V_S,\qquad
g_{U\setminus S}=g_U+g_S-2W(S,V\setminus U).
\]

Substituting these identities into the affected terms of \(H^T\) gives an
exact path-local graft delta. The planned theorem is:

> **Exact graft-delta theorem.** The structural-entropy change of a legal
> rooted subtree prune-and-regraft is determined entirely by cached statistics
> on the two affected ancestor paths and cross weights involving \(S\).

The formula will first be generated symbolically and checked against complete
recomputation on random weighted graphs. Only after agreement within
\(10^{-9}\) will it replace full scoring in the search loop.

### 3.4 Search modes and honest certificates

Two modes must be distinguished:

- **Exhaustive graft mode:** enumerate every legal ordered pair \((S,Q)\).
  Termination certifies that no improving NNI or graft exists in this declared
  neighborhood. This is suitable for the five exact misses and other small
  graphs.
- **Screened graft mode:** rank targets using graph-only signals such as
  cross-weight density \(W(S,Q)/(V_SV_Q)\), retain the top \(k\), then score
  them exactly. This scales better, but certifies only the inspected pool.

Cross-weight screening is a heuristic, not a safe pruning rule, until a valid
lower bound on the graft delta is proved.

### 3.5 Parallelism

Candidate scores are independent within a frozen sweep. Sources can be split
across CPU workers, and source--target pairs can later be batched on a GPU.
GPU acceleration is not part of the novelty claim and is unnecessary for the
first gate. A useful implementation should first exploit sparse CPU path
statistics; GPU work is justified only after profiling shows candidate scoring,
not tree copying or Python allocation, is the bottleneck.

## 4. Why this can strengthen the paper

The extension would add a genuinely different result rather than one more
baseline:

1. **A larger exact move family.** NNI repairs one internal edge; grafting can
   relocate a distant module in one accepted operation.
2. **A stronger local certificate.** Exhaustive termination certifies both NNI
   and subtree-graft neighborhoods.
3. **An explanation of the residual failures.** The five exact misses become
   case studies showing whether their obstruction is a shallow barrier, a
   distant reattachment, or something outside both neighborhoods.
4. **A bridge between graph compression and scalable hierarchical
   clustering.** PERCH/GRINCH supply routing and rearrangement ideas; NEST-G
   supplies an exact label-free information objective and verification.

Merely running PERCH and GRINCH as additional rows would not provide these
contributions. Their input assumptions and objectives differ, so raw scores
would be secondary evidence only.

### Preliminary novelty check

The checked literature contains child--aunt interchange for hierarchical
clustering objectives, GRINCH-style linkage grafting, and subtree
prune-and-regraft search for phylogenetic objectives. I did not find a prior
method that derives an exact subtree-graft delta for full graph tree structural
entropy and uses it for verified search. This is a provisional novelty result,
not permission to make a first-of-kind claim: a broader citation search and a
formula-level comparison with structural-entropy join/lift operators are part
of the pre-writing gate.

## 5. Experiments

### Phase 1: decisive exact-miss audit

Run exhaustive graft search from the selected NEST endpoint on all five misses.
For each graph record:

- starting and final \(H^T\);
- exact optimum and remaining gap;
- best graft source and target leaf sets;
- tree distance or number of NNI moves between endpoints when computable;
- number of legal grafts, accepted grafts, and subsequent NNI moves;
- runtime and peak memory; and
- whether the global optimum was reached.

Also run on 20 already-solved graphs as a negative control. Since acceptance is
monotone, entropy cannot regress; the control tests numerical and topology
correctness.

### Phase 2: operation and fairness ablations

Use identical starting trees and candidate budgets:

1. NNI descent only;
2. NNI + current bounded two-move escape;
3. NNI + exhaustive graft, where tractable;
4. NNI + top-\(k\) graph-linked graft proposals;
5. NNI + random graft proposals with the same candidate count;
6. GRINCH-style linkage proposals + exact entropy acceptance; and
7. full NEST-G.

This isolates whether improvement comes from the graft neighborhood, the
proposal rule, or simply evaluating more candidates.

### Phase 3: benchmark suite

Retain the five frozen 64-vertex HSBM regimes, but add regimes where nonlocal
repair should matter:

- chain-connected communities;
- sparse bridge communities;
- an adversarial arrival-order tree frozen before offline repair;
- crossed subtrees whose correct modules are far apart; and
- deeper hierarchical SBMs with four or more levels.

Use at least 100 independently generated graphs per regime. Report paired mean
difference and 95% confidence interval for \(H^T\), exact-hit rate where an
exact solver is feasible, hierarchy recovery, pair-F1, runtime, peak RAM,
candidate count, and accepted-move count.

### Phase 4: faithful PERCH/GRINCH comparison

- On vector datasets, run official PERCH and GRINCH with their documented
  distance/linkage inputs and report dendrogram purity plus runtime.
- On graph datasets, do not silently invent Euclidean features for PERCH.
  Either use a declared graph embedding as a separate condition or omit PERCH
  from the primary graph table.
- GRINCH can use a declared graph linkage, but its output must be independently
  rescored with \(H^T\). It remains a linkage baseline, not an SE optimizer.
- Apply NEST and NEST-G as post-processors to PERCH/GRINCH outputs to test
  initializer independence.

### Phase 5: scaling

Measure \(n\), \(m\), tree height, legal and retained graft counts, scoring
time, full verification time, and memory. Compare exhaustive, top-\(k\), and
parallel modes. Start at \(n=64,128,256,512,1024\); proceed further only when
the previous size stays within the declared resource cap.

## 6. Gate

### GO for enhancing the paper

Proceed if all of the following hold:

- exhaustive grafting reaches the exact optimum on at least 4 of the 5 current
  misses;
- predicted deltas match full recomputation within \(10^{-9}\) on every unit
  and randomized test;
- screened NEST-G beats NEST on at least 3 of the 5 nonlocal-stress regimes
  with paired 95% intervals excluding zero;
- the gain is not explained by a larger candidate budget in the random-graft
  control; and
- the screened implementation costs at most 2x NEST runtime at \(n=1024\), or
  establishes a clearly better entropy--runtime frontier.

### NO-GO

Do not enlarge the method if exhaustive grafting repairs at most one miss, if
the same gains arise from equal-budget random proposals, or if candidate
scoring is prohibitively quadratic without a defensible pruning rule. In that
case, expand related work and report the five failure structures internally,
but keep the submitted NEST method unchanged.

## 7. Immediate implementation plan

1. Add topology-only `_graft_candidates` and `_do_graft` utilities beside the
   NNI utilities in `selib/htree.py`.
2. Add exhaustive full-rescore tests on all rooted binary trees up to small
   \(n\), checking legality, leaf preservation, binarity, and monotonic commit.
3. Reconstruct the five frozen graph/endpoint pairs from their manifests and
   rerun the exact-miss audit without using the optimum in move selection.
4. Derive and test `graft_delta`; retain the full recomputation as an
   independent verifier.
5. Only after Phase 1 passes, add screened candidates, multiprocessing, and the
   expanded benchmark.

No GPU rental is needed for Phases 1--3. Four CPU workers and under 8 GB RAM
are sufficient. The first audit should run locally or on idle CPU without
touching unrelated jobs.

## 8. Sources

- Kobren et al., *A Hierarchical Algorithm for Extreme Clustering*, KDD 2017:
  https://arxiv.org/abs/1704.01858
- Official PERCH implementation:
  https://github.com/iesl/xcluster
- Monath et al., *Scalable Hierarchical Clustering with Tree Grafting*, KDD
  2019: https://arxiv.org/abs/2001.00076
- Official GRINCH implementation:
  https://github.com/iesl/grinch
- Jowhari, *Hierarchical Clustering via Local Search* (interchange under the
  Moseley--Wang revenue objective): https://arxiv.org/abs/2405.15983
