## Progress: constrained hardness theorem now has a precise source problem

The source theorem is cubic Minimum Edge Bisection: the problem remains
NP-complete on 3-regular graphs (Bui, Chaudhuri, Leighton, and Sipser,
`Combinatorica` 7(2), 1987, DOI `10.1007/BF02579448`; explicitly restated in
Díaz et al., `JCSS` 144, 2024, Article 103550).

For a simple unweighted cubic graph with even `n`, `m=3n/2`, and a balanced
two-module partition `P` with cut size `c(P)`, our derived objective becomes

```text
H^P(G) = log_2(n/2) + c(P)/m.
```

Therefore minimizing balanced two-module 2D structural entropy is exactly
Minimum Bisection, proving NP-hardness of this constrained SE optimization even
on cubic graphs.

Scope boundary: this does not yet prove hardness for unconstrained fixed-`K`
SE or unrestricted TREE-SE. Exhaustive enumeration already found regular
graphs whose best unconstrained two-module SE partition is unbalanced, so a
balance-forcing gadget or different reduction is still required.

Detailed derivation and source records:

- `research/se-hier-nni/TCS_HARDNESS_WORKLOG.md`
- `research/se-hier-nni/TCS_PRIMARY_SOURCES.bib`
- `results/tcs_balanced_se_bisection_check.json`
- `results/tcs_unconstrained_two_module_counterexamples.json`
