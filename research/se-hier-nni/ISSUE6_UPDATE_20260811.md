## Progress: first exact reduction identity verified

Derived the partition-dependent form

```text
H^P(G) = C_G + (1/vol(G)) sum_i
         [2 e_i log_2 V_i + g_i log_2 vol(G)].
```

For a loop-free regular graph and a balanced two-module partition, both module
volumes equal `vol(G)/2`. Therefore, for any two balanced partitions `P,Q`,

```text
H^P(G) - H^Q(G) = [cut(P)-cut(Q)] / |E|.
```

Thus balanced two-module SE minimization is exactly Minimum Bisection on this
class. It is not directly Max-Cut: lower structural entropy corresponds to a
smaller cut.

Finite falsification/regression check:

- 23 regular graphs;
- 3,199 balanced partitions;
- zero objective-ordering failures;
- maximum closed-form error `1.3322676295501878e-15`;
- maximum affine-difference error `7.771561172376096e-16`.

Artifacts:

- `research/se-hier-nni/TCS_HARDNESS_WORKLOG.md`
- `scripts/check_balanced_se_bisection.py`
- `results/tcs_balanced_se_bisection_check.json`

This establishes a promising lemma for the **balanced constrained** variant,
not yet NP-hardness of unconstrained fixed-`K` SE or unrestricted TREE-SE.
Next proof obligations are to fix the precise regular Minimum Bisection source
theorem and remove the balance/height restrictions with a forcing construction
or a direct reduction. The peer's constrained/overlapping-SE proof should be
checked for reusable gadgets and overlap in theorem scope.
