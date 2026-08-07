# TAMC 2026 EasyChair fields

Use these fields verbatim unless EasyChair imposes a shorter field limit.
Author identities belong in EasyChair only; the review PDF is double-blind.

## Title

NNI-Certified Structural-Entropy Hierarchies: Fast Refinement beyond Greedy
Construction

## Abstract

Structural entropy evaluates a graph hierarchy through the description length
of an encoding tree, but a hierarchy produced by merging, partitioning, or
stretch-compress construction need not be locally optimal in tree space. We
introduce SE-NNI, an exact refinement method based on rooted nearest-neighbor
interchange (NNI). For weighted graphs, we derive a closed form for the entropy
change of an NNI move using only three module volumes and two cross-module edge
weights. This supports monotone best-improvement descent and a checkable
one-NNI local-optimality certificate. We further introduce a bounded two-move
search that may cross a controlled intermediate barrier but commits only an
entropy-decreasing pair, and a fast multi-start constructor that refines SE
agglomeration, recursive SE, and Paris candidates. All synthetic comparisons
are paired by graph seed and use the same independently recomputed tree
objective. Across 50 seeded graphs from five hierarchical regimes, SE-NNI
attains the lowest mean entropy in every regime. Relative to the previous
se_hier implementation, it lowers entropy by 0.0279 plus or minus 0.0072 bits,
raises fine-level dendrogram purity by 0.016 plus or minus 0.010, and is 21.5
times faster under the instrumented benchmark. The NNI audit also finds
strictly improving moves in common SE and non-SE constructors, demonstrating
that construction quality and local tree optimality are distinct concerns.

## Keywords

Enter one per line:

```text
structural entropy
hierarchical clustering
nearest-neighbor interchange
local search
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
