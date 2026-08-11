# TCS Journal Proposal: Complexity and Certified Rich-Move Search for Structural-Entropy Hierarchies

**Target:** *Theoretical Computer Science*, Algorithms, Automata, Complexity and Games

**Journal objective:** Extend the submitted TAMC paper into a theory-led journal
article that classifies the computational difficulty of structural-entropy
hierarchy optimization and develops exact, certified search over both local NNI
and nonlocal graft neighborhoods.

**Conference reference state:** `tamc2026-submitted` at commit `7e93199`

**Related issues:** #1 (fast verified execution), #2 (graft and richer moves),
#3 (general hierarchical objectives), and #5 (five residual exact misses)

**Primary tracking issue:** #6

**Current implementation status (2026-08-11):** the correctness-first rooted
subtree graft and an independent edge--LCA delta evaluator are implemented on
`codex/nest-entropy-grafting`. Across 1,680 legal random weighted-tree moves,
the predicted delta agrees with full objective recomputation to at most
`1.41e-15` bits. Applying exhaustive graft refinement to every one of the 32
frozen coalescent candidates closes all five previously reported exact-optimum
misses at `n=12,14,16`. This is a diagnostic result on preidentified failures,
not the final matched-neighborhood evaluation.

## TL;DR

The TAMC paper proves an exact structural-entropy change formula for rooted NNI,
uses it to produce one-NNI certificates, and audits the resulting search against
exact optima on small graphs. The journal extension will answer the harder
questions that the conference paper leaves open:

1. Is globally minimizing tree structural entropy computationally hard?
2. Which constrained variants are hard, and which restrictions are tractable?
3. How much stronger is subtree grafting than one- or two-NNI search?
4. Which hierarchy objectives admit exact NNI and graft deltas?
5. Can the resulting algorithm return a checkable certificate for a declared
   rich neighborhood while scaling beyond exhaustive rescoring?

The target result is not merely a faster NEST implementation. It is a formal
theory of structural-entropy hierarchy optimization, supported by a certified
NNI-plus-graft algorithm and reproducible exact audits.

## 1. Baseline and journal gap

The submitted paper considers a fixed undirected nonnegative weighted graph
`G=(V,E,w)` and an encoding tree `T` whose leaves are vertices. For total
volume `2m=sum_v d_v`, module volume `V_alpha`, and module cut `g_alpha`,

```text
H^T(G) = - sum_{alpha != root}
           (g_alpha / 2m) log_2(V_alpha / V_parent(alpha)).
```

It currently contributes:

- an exact local NNI delta;
- monotone NNI descent and a one-NNI local-optimality certificate;
- a bounded two-move escape;
- an `O(3^n)`-time, `O(2^n)`-memory exact subset dynamic program; and
- empirical exact-hit and constructor-refinement audits.

For a full TCS paper, three gaps remain:

- no hardness or tractability classification for the global objective;
- no theory comparing local NNI and nonlocal graft neighborhoods; and
- no general characterization of objectives that support exact certified tree
  edits.

## 2. Formal problem family

The proof program must define each variant separately. Hardness for one variant
must not be silently transferred to another.

### 2.1 Unrestricted Tree Structural Entropy

**TREE-SE.** Given a nonnegative rational weighted undirected graph `G`, find a
rooted encoding tree `T` minimizing `H^T(G)`.

**Decision form.** Given `G` and a threshold represented in a comparison-safe
form, decide whether some `T` has objective at most the threshold.

The arithmetic model requires care because the objective contains logarithms.
The proof should either:

- construct instances whose relevant volumes are powers of two, so all
  compared terms are rational multiples of integer logarithms;
- compare an equivalent exponentiated product objective; or
- state NP-hardness for the optimization problem without prematurely claiming
  membership in NP.

### 2.2 Height-2 and fixed-number variants

**2D-SE-K.** Minimize structural entropy over height-2 encoding trees with
exactly `K` nonempty top-level modules.

Important subcases:

- `K=2` with unconstrained module volumes;
- balanced `K=2` or prescribed module volumes;
- fixed constant `K` versus `K` supplied as input; and
- unweighted, regular, bounded-degree, and general weighted graphs.

These variants are the most plausible starting point for a graph-partitioning
reduction.

### 2.3 Height-bounded and binary variants

**HEIGHT-SE-h.** Minimize over trees of height at most `h`.

**BINARY-SE.** Minimize over rooted binary encoding trees. Binary sufficiency
relates this variant to TREE-SE for optimization, but the reduction and decision
form still need to be stated carefully.

### 2.4 Overlapping and constrained variants

A peer reports a recent NP-hardness result for constrained structural entropy
with a given cluster count and overlapping membership. We will obtain and read
the exact manuscript, theorem, objective, graph assumptions, and reduction.

This result is prior work and a possible source of gadgets. It does **not** by
itself prove hardness of TREE-SE because:

- overlapping memberships are not ordinary disjoint encoding-tree modules;
- fixing `K` changes the feasible set; and
- hardness of a restriction does not transfer to a relaxation unless a
  polynomial gadget forces every optimum of the relaxed instance to satisfy
  the restriction.

## 3. Hardness program

### 3.1 First target: fixed-`K` two-level hardness

Derive the exact partition-dependent form of two-dimensional structural
entropy. For a partition `P={S_1,...,S_K}`, simplify all terms that are constant
with respect to `P`. Determine precisely how module volumes, internal weights,
and cut weights enter the objective.

Candidate reductions, in preferred order:

1. **Minimum Bisection / balanced graph partition.** For regular graphs with
   fixed module volumes, SE minimization naturally rewards internal edge weight
   and penalizes cross-module weight. This appears more direct than Max-Cut.
2. **Max-Cut through complement or sign-free gadgets.** Explore the peer's
   suggested Max-Cut route, but retain nonnegative weights and prove that the
   entropy ordering is reversed exactly. Do not introduce negative edges,
   because they violate the SE definition used by the paper.
3. **Minimum `K`-cut, densest partition, or correlation clustering.** Use these
   if their objective matches the simplified SE expression more faithfully.

The selected reduction must prove both directions and control degree-dependent
volume terms; a resemblance to cut optimization is insufficient.

### 3.2 Transfer to unrestricted trees

If 2D-SE-K is NP-hard, build a polynomial-size forcing construction showing
that an optimal unrestricted encoding tree encodes the required top-level
partition. Candidate mechanisms include:

- replicated or high-weight anchor gadgets that force prescribed modules;
- scale-separated weights that make extra hierarchy levels neutral or more
  expensive; and
- a normal-form theorem that flattens every optimal tree for the constructed
  instances without increasing entropy.

Only after such a lemma may constrained hardness be transferred to TREE-SE.

### 3.3 Positive results

Hardness alone is not enough for the journal paper. Investigate:

- polynomial algorithms on cliques, trees, paths, stars, complete multipartite
  graphs, ultrametric graphs, and exact hierarchical block graphs;
- fixed-parameter algorithms parameterized by `n`, height, number of modules,
  treewidth, or cut size;
- approximation or lower-bound guarantees; and
- whether the existing subset DP can be improved for any restricted family.

### 3.4 Proof-validation protocol

Before writing a theorem:

1. symbolically derive the reduced objective;
2. exhaustively enumerate all partitions/trees for small source instances;
3. generate the reduced SE instance;
4. verify the claimed if-and-only-if correspondence computationally;
5. search automatically for the smallest counterexample to each lemma; and
6. freeze successful checks as regression tests.

Computation can falsify a proposed proof or validate finite algebraic cases,
but the paper must still contain a complete mathematical proof.

## 4. Rich tree operations

The journal algorithm will include the following declared neighborhoods.

### 4.1 Rooted NNI

Retain the submitted exact NNI delta and one-NNI certificate. Generalize the
delta to the objective class developed under issue #3 when possible.

### 4.2 Bounded compound NNI

Retain the two-move barrier-crossing mechanism as a bounded search baseline.
Formalize which endpoints it can reach and construct families that require
more than two local rotations.

### 4.3 Subtree prune-and-regraft

A legal graft selects a non-root source subtree `S` and a target subtree `Q`
that is neither an ancestor nor descendant of `S`; it detaches `S`, suppresses
the resulting unary node, and inserts a new binary parent for `S` and `Q`.

Required results:

- exact full-rescore reference implementation;
- exact path-local structural-entropy delta;
- proof that only the removal and insertion ancestor paths contribute;
- exhaustive NNI-plus-graft local certificate on small graphs;
- screened graft mode with an explicitly limited certificate; and
- regression checks against full objective recomputation within `1e-9`.

### 4.4 Neighborhood comparison theory

Prove or falsify:

- every graft can be decomposed into a bounded sequence of NNIs;
- upper and lower bounds on the required NNI path length;
- families where every improving path of NNIs crosses a positive barrier but
  one graft improves immediately;
- strict containments among one-NNI, two-NNI, and graft local optima; and
- graph or objective conditions under which the neighborhoods become
  equivalent.

These results turn grafting from an engineering addition into a theoretical
contribution.

## 5. General objective framework

Issue #3 will be developed around edge-LCA additive objectives of the form

```text
F_phi(T;G) = sum_{uv in E} w_uv
             phi(V_lca_T(u,v), d_u, d_v, global statistics).
```

Research questions:

- Which algebraic conditions on `phi` yield an exact local NNI delta?
- Which yield a path-local graft delta?
- When can cached module statistics evaluate a move sublinearly in `n`?
- Which lower bounds or curvature properties predict local traps?

Initial instances are tree structural entropy, Dasgupta cost, and
Moseley--Wang revenue. At least two non-equivalent objectives must pass
formula-versus-full-rescore tests before this becomes a journal claim.

## 6. Algorithmic and experimental evidence

### 6.1 Exact hard-case audit

Use issue #5's five residual misses as diagnostics, not as the final test set.
Recover optimal and returned trees, objective decompositions, shortest feasible
NNI paths, barrier heights, and best grafts. Freeze the resulting hypothesis
before generating new evaluation instances.

The first diagnostic gate has passed: the recorded NEST endpoints were
reconstructed exactly and NNI-plus-graft reaches the exact optimum on all five
cases. The next gate is to freeze the richer method and test it on a new sealed
suite, so these five cases cannot serve as confirmatory evidence.

### 6.2 Matched-neighborhood study

From identical initial trees compare:

- one-NNI descent;
- bounded two-NNI escape;
- exhaustive graft where feasible;
- screened graft;
- equal-count random graft proposals; and
- adaptive NNI-plus-graft search.

Match candidate evaluations or wall-clock budgets. Report objective gap,
exact-hit rate, time-to-target, moves, runtime, memory, and 95% confidence
intervals.

### 6.3 Theory-directed graph families

Add constructed families that separate the neighborhoods, plus hierarchical
SBMs of increasing depth, sparse bridges, crossed subtrees, imbalanced graphs,
and real weighted networks. Every constructed family must have a stated
theoretical purpose.

### 6.4 Scalability

Use issue #1's fast mode only after exact deltas are validated. Report
asymptotic candidate counts and empirical scaling. Parallel CPU evaluation is
useful; GPU batching is optional engineering evidence, not a novelty claim.

## 7. Falsification and decision gates

### Hardness gate

Continue with a claimed reduction only if:

- the target SE decision/optimization problem is precisely specified;
- all weights and gadgets have polynomial encoding size;
- both reduction directions are proved;
- logarithmic comparisons are handled exactly;
- small exhaustive instances contain no counterexample; and
- the theorem is not already implied by the peer's or another public result.

If the Max-Cut route fails, report why and move to Minimum Bisection or another
objective-faithful source problem. Do not force a Max-Cut story.

### Graft gate

Promote grafting into the journal method only if:

- the exact delta matches full rescoring within `1e-9`;
- it repairs at least four of the five known misses or establishes a rigorous
  strict-neighborhood separation;
- it wins on new nonlocal-stress instances under matched budgets; and
- screened search offers a defensible entropy-runtime frontier.

### Generalization gate

Claim a general framework only if at least two non-equivalent objectives share
the theorem and executable interface. Otherwise keep the paper explicitly
structural-entropy-specific.

## 8. Expected journal contributions

A successful paper should contain:

1. a hardness/tractability classification for structural-entropy hierarchy
   optimization;
2. exact NNI and graft calculus, with objective-class conditions;
3. formal separation and relationship results for local and nonlocal tree
   neighborhoods;
4. a certified NNI-plus-graft algorithm with analyzed complexity;
5. exact and theory-directed empirical audits; and
6. a reproducible implementation, manifests, proofs, and verification tests.

## 9. Immediate work plan

1. Obtain the peer's constrained/overlapping-SE NP-hardness manuscript or
   theorem statement and construct a claim-comparison matrix.
2. Derive the partition-dependent form of 2D-SE-K and test candidate reductions
   from Minimum Bisection and Max-Cut on exhaustive small instances.
3. Reconstruct issue #5's five misses and run exhaustive full-rescore grafting.
4. Derive the exact graft path delta and regression-test it.
5. Use the successful hardness and neighborhood results to choose the final
   journal theorem spine before expanding experiments.

## 10. Scope discipline

- Semi-supervised constraints in issue #4 remain a separate paper.
- Direct PERCH/GRINCH comparisons are secondary unless inputs are faithful.
- More datasets cannot substitute for a missing theorem.
- A constrained or overlapping hardness theorem must be cited and differentiated,
  not repackaged as unrestricted TREE-SE hardness.
- The TAMC paper remains immutable and is cited transparently as the conference
  predecessor of any journal submission.
