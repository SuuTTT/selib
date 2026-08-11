# TCS first-draft status

This directory is a journal manuscript derived from, but independent of, the
frozen TAMC submission in `../se-hier-nni/`.

## Evidence already integrated

- Balanced two-module SE is NP-hard on simple unweighted cubic graphs.
- The balanced regular identity was checked on 23 graphs and 3,199 balanced
  partitions with maximum error `1.34e-15`.
- The exact NNI identity and the frozen 500-graph / 375-graph audits are retained.
- The edge--LCA and changed-incidence graft formulas are stated independently.
- Graft deltas were checked on 1,680 legal moves with error near machine precision.
- Exhaustive graft refinement repaired all five diagnosed NEST exact misses.

## Evidence required before journal submission

1. Freeze NEST-G and run a new sealed matched-budget suite rather than only the
   five known misses.
2. Implement and benchmark the cached path scorer.
3. Add a formal NNI-sequence bound for simulating a graft and a clean strict
   separation family.
4. Attempt a balance-forcing reduction for unconstrained 2D-SE or state the
   constrained theorem as the final complexity boundary.
5. Validate the edge--LCA framework on at least two non-equivalent objectives
   before promoting it to a general theorem.

## Claim--evidence map

| Claim | Evidence | Status |
|---|---|---|
| Balanced two-module SE is NP-hard on cubic graphs | Lemma 1 + Minimum Bisection reduction | Supported |
| Exact NNI delta | Symbolic proof + existing regression suite | Supported |
| Exact graft delta | Two proofs + 1,680-move validator | Supported |
| Graft contains NNI | Constructive proposition | Supported |
| Graft repairs the five observed NEST misses | Exact diagnostic JSON | Supported, diagnostic |
| NEST-G improves future instances under matched budgets | No new sealed suite yet | Needs evidence |
| Unrestricted TREE-SE is NP-hard | No forcing/normal-form reduction yet | Unsupported; omitted |

## Build

Use the `latex-paper-en` compile helper on `main.tex`. The draft uses the
Elsevier `elsarticle` preprint layout and the numbered reference style.
