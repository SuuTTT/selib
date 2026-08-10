# TAMC 2026 EasyChair fields

Use these fields verbatim unless EasyChair imposes a shorter field limit.
Author identities belong in EasyChair only; the review PDF is double-blind.

## Title

NEST: Locally Certified Search for Structural-Entropy Hierarchies

## Abstract

Structural entropy evaluates a graph hierarchy through the description length
of an encoding tree. Existing methods such as HCSE and BBM construct such
trees, but do not determine whether a returned hierarchy still admits an
entropy-reducing local topology change. We introduce NNI-certified Entropy
Search over Trees (NEST), a multi-start optimizer based on rooted
nearest-neighbor interchange (NNI). For weighted graphs, we derive the exact
entropy change of one NNI and prove that an improving rotation can be
inaccessible to a monotone single merge or compression. The exact formula lets
NEST score every one-step NNI move without rebuilding the tree and repeatedly
take the largest entropy decrease. When no improving move remains, the output
is certified locally optimal under one NNI. A better tree may nevertheless
require a temporary increase, so NEST also searches a bounded set of two-move
paths and accepts a path only when its final tree improves the starting tree.
Using the known binary-sufficiency
property of structural entropy, we formulate an O(3^n) arbitrary-subset
specialization of trellis inference and a global-optimum audit on small graphs. Across
50 graphs from five 64-vertex hierarchical regimes, NEST lowers entropy by
0.4290 plus or minus 0.0281 bits relative to the better of HCSE and BBM and wins
all paired comparisons. On a new sealed, candidate-budget-matched audit of 250
independently generated 12-vertex graphs, 32 coalescent starts reach the exact
global optimum on 249/250 instances, versus 2/250 for 32 HCSE calls and 1/250
for either 32-call BBM variant. The sole NEST miss has a 0.07990% relative gap.
These results certify observed optimality on the declared suite without
asserting a general approximation ratio.

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
