# TCS Manuscript Spine

## Working title

**Certified Local and Nonlocal Search for Structural-Entropy Hierarchies**

The subtitle can mention complexity only after the unrestricted hardness gate
is resolved. The current proved hardness result is for a balanced height-2
restriction and must not be presented as TREE-SE hardness.

## One-sentence story

Structural-entropy hierarchy optimization contains a provably hard balanced
partitioning core, while its tree space admits exact local and nonlocal edit
deltas; combining NNI and subtree grafting yields checkable neighborhood
certificates and repairs the failures of rotation-only search.

## Contribution order

1. **Complexity classification.** Prove NP-hardness of balanced two-module 2D
   structural entropy on simple unweighted cubic graphs through an exact affine
   equivalence with Minimum Bisection. State unconstrained and unrestricted
   variants separately.
2. **Exact edit calculus.** Retain the exact weighted NNI identity and derive
   the exact edge--LCA graft delta, with a formal affected-path theorem.
3. **Neighborhood theory.** Prove that rooted NNI is a special case of graft,
   so graft-locality implies NNI-locality; establish strict separation through
   constructed or exhaustively certified witnesses and bound NNI sequences
   that realize a graft.
4. **Certified algorithm.** Give exhaustive NNI-plus-graft descent with full
   endpoint verification, then a cached path scorer and screened scalable mode
   whose weaker certificate is named explicitly.
5. **Reproducible evaluation.** Use the five old misses only for mechanism
   discovery, then freeze the method and run new sealed, candidate- or
   wall-clock-matched suites with exact optima where feasible.

## Theorem dependency chain

```text
cubic Minimum Bisection hardness
        |
        v
balanced 2D-SE affine identity ---> constrained NP-hardness

edge--LCA expansion ---> exact graft delta ---> monotone verified graft search
        |                         |
        |                         v
exact NNI identity ---> NNI is a graft special case
                                  |
                                  v
                    rich-neighborhood certificate
```

The two chains are logically independent: failure to transfer hardness to
unrestricted trees does not invalidate the edit calculus, and successful graft
search does not prove global tractability.

## Proposed section structure

1. Introduction and problem variants
2. Structural entropy and edge--LCA preliminaries
3. A hard balanced partitioning core
4. Exact calculus for NNI and subtree grafts
5. Relations and separations among tree neighborhoods
6. Certified NNI-plus-graft search
7. Exact audits and matched-neighborhood experiments
8. General edge--LCA objectives
9. Discussion and open complexity questions

Appendices contain the full hardness proof, path-local graft proof, exhaustive
counterexample protocols, implementation invariants, and sealed manifests.

## Current evidence gates

| Claim | Current status | Required before manuscript claim |
|---|---|---|
| Balanced 2D-SE is NP-hard on cubic graphs | algebra and source theorem identified | formal proof written and independently checked |
| Unrestricted TREE-SE is NP-hard | open | valid forcing/normal-form reduction |
| Exact graft delta | formula implemented; 1,680 moves agree to 1.41e-15 | affected-path proof and cached implementation |
| Graft strictly strengthens NNI in practice | five NNI failures repaired | frozen witness plus new sealed evaluation |
| NNI is a special graft | direct topology argument | formal proposition and diagram |
| NNI-plus-graft improves general performance | unknown | matched suite with confidence intervals |
| Approximation guarantee | unknown | complete proof or omit |

## Claims that must not enter the paper yet

- TREE-SE is NP-hard.
- Fixed-`K` unconstrained 2D-SE is NP-hard.
- Five repaired diagnostic cases estimate a population success probability.
- Graft search is globally optimal in general.
- The all-edge reference delta is already the scalable path-cached algorithm.
- The peer's overlap/fixed-cluster result transfers to disjoint encoding trees.
