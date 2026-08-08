# TAMC 2026 EasyChair fields

Use these fields verbatim unless EasyChair imposes a shorter field limit.
Author identities belong in EasyChair only; the review PDF is double-blind.

## Title

NEST: Structural-Entropy Hierarchy Search with General Tree Editing and Exact
NNI Certification

## Abstract

Structural entropy evaluates a graph hierarchy through the description length
of an encoding tree. Existing methods such as HCSE and BBM construct such
trees, but do not determine whether a returned hierarchy still admits an
entropy-reducing local topology change. We introduce two complementary tree
optimizers. Entropy-Guided Tree Editing (EGTE) constructs a hierarchy from
multiple initial trees and monotonically improves the complete objective by
level collapse and subtree relocation. NNI-certified Entropy Search over Trees
(NEST) replaces this costly general-edit stage with exact rooted
nearest-neighbor interchange (NNI). For weighted graphs, we derive a closed
form for the entropy change of an NNI using only three module volumes and two
cross-module edge weights. The identity supports monotone best-improvement
descent, a checkable one-NNI local-optimality certificate, and a bounded
two-move search that can cross a controlled intermediate barrier while
committing only an entropy-decreasing endpoint. All synthetic comparisons are
paired by graph seed and use the same independently recomputed objective.
Across 50 graphs from five hierarchical regimes, NEST attains the lowest mean
entropy in every regime. Relative to the better of HCSE and BBM on each graph,
it lowers entropy by 0.4290 plus or minus 0.0281 bits and wins all 50 paired
comparisons. As an internal efficiency comparison, NEST also lowers entropy by
0.0279 plus or minus 0.0072 bits while running 21.5 times faster than EGTE
under the instrumented benchmark.

## Keywords

Enter one per line:

```text
structural entropy
hierarchical clustering
nearest-neighbor interchange
tree editing
graph algorithms
```

## Best-fitting TAMC topics

1. Computational complexity and algorithms
2. Information calculus
3. Computational geometry and graph theory
4. Combinatorial optimization

## Private author fields

For every author, EasyChair requires the real name, email, country,
affiliation, and corresponding-author setting. At least one corresponding
author must have an EasyChair account. Do not insert these identities into the
double-blind PDF.

## Student-paper award

Select/request this only if **all** authors are full-time students at
submission time. If eligible, the official CFP requires an explicit final line
in the abstract; the present package does not claim eligibility.
