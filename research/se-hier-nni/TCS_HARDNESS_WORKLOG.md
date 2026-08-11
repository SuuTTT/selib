# TCS Hardness Worklog

## 2026-08-11: balanced regular two-module identity

### Status

The first reduction lemma has an exact algebraic candidate and a finite
verification script. It establishes a clean route from **Minimum Bisection** to
a balanced height-2 structural-entropy problem. It does not yet establish
hardness of unconstrained fixed-`K` SE or unrestricted encoding-tree SE.

### Partition-dependent form of 2D structural entropy

Let `M=vol(G)=sum_v d_v`. For a partition `P={S_1,...,S_K}`, write `V_i` for
module volume, `g_i` for its cut, and `e_i` for its internal edge weight. From
the canonical definition,

```text
H^P(G)
 = -(1/M) sum_v d_v log_2(d_v/V_{c(v)})
   -(1/M) sum_i g_i log_2(V_i/M)

 = C_G + (1/M) sum_i [(V_i-g_i) log_2 V_i + g_i log_2 M]

 = C_G + (1/M) sum_i [2 e_i log_2 V_i + g_i log_2 M],
```

where `C_G=-(1/M)sum_v d_v log_2 d_v` is independent of the partition and
`V_i-g_i=2e_i` for an undirected graph.

This derivation shows why degree and volume control are essential in a
hardness reduction: without fixed module volumes, SE is not simply a cut
objective.

### Exact balanced regular specialization

Suppose `G` is loop-free, `d`-regular, and has even `n`. Restrict to two
modules with exactly `n/2` vertices each. Both modules then have volume `M/2`.
If `c(P)` is the cut weight and `m=M/2` is total edge weight, then total
internal edge weight is `m-c(P)`, so

```text
H^P(G)
 = C_G
   + [2(m-c(P))/M] log_2(M/2)
   + [2c(P)/M] log_2 M.
```

Consequently, for any two balanced partitions `P` and `Q`,

```text
H^P(G) - H^Q(G) = [c(P)-c(Q)]/m.
```

Therefore a balanced bipartition minimizes 2D structural entropy if and only if
it is a minimum bisection. The relation is strictly increasing and involves no
approximation.

### Implication and remaining proof obligations

The source theorem is now identified. Bui, Chaudhuri, Leighton, and Sipser
(`Combinatorica` 7(2), 1987, DOI `10.1007/BF02579448`) establish the regular
graph bisection result; D\'iaz et al. (`JCSS` 144, 2024, Article 103550)
explicitly restate that Minimum Edge Bisection remains NP-complete for
`d=3` and cite Bui et al. for that statement.

Together with the identity above, this gives the following **constrained
hardness theorem**:

> Minimizing two-dimensional structural entropy over balanced two-module
> partitions is NP-hard even for simple unweighted cubic graphs.

Indeed, a cubic graph on even `n` vertices has `m=3n/2` edges, and every
balanced side has volume `m`. For a balanced partition `P` with cut size
`c(P)`, the objective simplifies further to

```text
H^P(G) = log_2(n/2) + c(P)/m.
```

The first term is fixed for the input graph, so an entropy minimizer is exactly
a minimum bisection. A polynomial optimizer for the constrained SE problem
would therefore solve cubic Minimum Bisection. We presently claim NP-hardness
of the optimization problem, not NP-completeness of a logarithmic-threshold
decision encoding.

Equivalently, the constrained problem is:

> Given a regular graph, find a height-2, two-module structural-entropy
> partition whose modules contain equally many vertices.

This is not yet the theorem desired for the journal paper. We still need one of:

1. a gadget proving that unconstrained exactly-two-module SE optima are
   balanced;
2. a direct reduction to unconstrained fixed-`K` 2D-SE; or
3. a normal-form/forcing result transferring the constrained hardness to
   unrestricted encoding trees.

### Max-Cut assessment

For the balanced regular specialization, minimizing SE minimizes the cut. It
does **not** maximize the cut. A Max-Cut reduction would therefore require a
complement construction or a nonnegative forcing gadget that exactly reverses
the ordering while preserving controlled degrees and volumes. Minimum
Bisection is presently the more direct source problem.

The reported peer result on fixed-cluster and overlapping SE may still provide
a useful gadget or citation. We must inspect its exact objective and feasible
set before using it.

### Computational check

Run:

```bash
.venv/bin/python scripts/check_balanced_se_bisection.py \
  --output results/tcs_balanced_se_bisection_check.json
```

The dependency-free script compares the closed form with a separate direct
implementation of the canonical 2D-SE definition and checks that entropy
minimizers coincide with minimum bisections on all tested balanced partitions.
Cross-checking the generated cases against `selib.metrics.structural_entropy_2d`
remains an independent validation step once the project environment imports
normally. This computation is a falsification and regression tool, not a
substitute for the mathematical proof.

### First run

Protocol `balanced-regular-2d-se-bisection-v1` completed successfully on:

- 23 regular graphs from cycle, complete, complete-bipartite, prism,
  M\"obius-ladder, and circulant families;
- 3,199 unordered balanced bipartitions;
- maximum closed-form error `1.3322676295501878e-15`;
- maximum affine-difference error `7.771561172376096e-16`; and
- zero cases where an entropy minimizer was not a minimum bisection.

Artifact: `results/tcs_balanced_se_bisection_check.json`.

This supports the algebraic identity at floating-point precision. The next
proof task is to attach it to a precise regular Minimum Bisection hardness
theorem and then remove the balance restriction with a forcing construction or
a direct unconstrained reduction.

## 2026-08-11: balance does not disappear automatically

The companion script
`scripts/search_unbalanced_se_counterexamples.py` enumerated all 13,697
unordered nontrivial bipartitions of the same 23 regular graphs. It compared
the best unconstrained exactly-two-module partition with the best balanced
partition.

Two counterexamples were found:

| Graph | Order | Best side sizes | Best unconstrained SE | Best balanced SE | Gap |
|---|---:|---:|---:|---:|---:|
| pentagonal prism | 10 | 4/6 | 2.625496659 | 2.655261428 | 0.029764769 bits |
| 10-vertex M\"obius ladder | 10 | 4/6 | 2.625496659 | 2.655261428 | 0.029764769 bits |

Thus regularity plus exactly two nonempty modules does not force a bisection.
The balanced Minimum-Bisection lemma cannot directly establish hardness of
unconstrained 2D-SE with `K=2`. A valid next reduction must enforce equal
volumes through a polynomial gadget, or start from a source problem whose
objective already matches the volume-sensitive SE expression.

Artifact: `results/tcs_unconstrained_two_module_counterexamples.json`.
