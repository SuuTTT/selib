# TAMC 2026 EasyChair fields

Use these fields verbatim unless EasyChair imposes a shorter field limit.
Author identities belong in EasyChair only; the review PDF is double-blind.

## Title

NEST: Locally Certified Search for Structural-Entropy Hierarchies

## Abstract

Structural entropy evaluates a graph hierarchy through the description length
of an encoding tree. HCSE and BBM construct such trees but do not determine
whether the result admits a local entropy-reducing topology change. We
introduce NNI-certified Entropy Search over Trees (NEST), a multi-start
optimizer based on rooted nearest-neighbor interchange (NNI). For weighted
graphs, we derive the exact NNI entropy change and prove that an improving
rotation can be inaccessible to a monotone merge or compression. The formula
supports best-improvement descent and a checkable one-NNI local-optimality
certificate. Because a better tree may require a temporary increase, NEST also
tests bounded two-move paths but commits only improving endpoints. We also
formulate an O(3^n) subset dynamic program, using binary sufficiency, to compute
exact global optima for audit graphs. Across 500 graphs
from five 64-vertex hierarchical regimes, NEST lowers entropy by 0.4239 plus or
minus 0.0086 bits relative to the better of HCSE and BBM and wins all 500 paired
comparisons. In sealed, candidate-budget-matched audits, 32 coalescent starts
reach the exact global optimum on 249/250, 99/100, and 22/25 instances at 12,
14, and 16 vertices, respectively (370/375 overall), whereas 32-call HCSE and
label-free BBM reach 2/375 and 1/375. The exact audits show that the local
certificate and bounded escape together recover global optima reliably across
the tested regimes and sizes.

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
