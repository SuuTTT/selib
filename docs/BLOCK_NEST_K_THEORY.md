# Block-NEST-K: exact fixed-K block refinement

Status: **experimental research implementation**. This document establishes the
algebra currently implemented and tested; it does not claim novelty or SOTA.

## Objective and notation

For an undirected weighted graph with total volume `M = 2m`, a partition
`P`, community volume `V_C`, and community cut `g_C`, write

```text
H2(G; P) = const(G) + sum_C Phi(V_C, g_C),
Phi(V, g) = (V/M) log2(V) - (g/M) log2(V/M).
```

The graph-only constant cancels in every partition comparison.

Consider a nonempty block `S` strictly contained in community `A`, moved to a
different existing community `B`. Let:

- `d_S = sum_{v in S} d_v` be its volume;
- `e_S` be the internal edge weight of `S`, with a self-loop counted once;
- `q_S = d_S - 2 e_S` be its boundary weight;
- `a = w(S, A without S)`; and
- `b = w(S, B)`.

The exact affected state is

```text
V'_A = V_A - d_S,    g'_A = g_A - q_S + 2a,
V'_B = V_B + d_S,    g'_B = g_B + q_S - 2b.
```

Therefore the exact move delta is

```text
Delta(S: A -> B) = Phi(V'_A, g'_A) + Phi(V'_B, g'_B)
                 - Phi(V_A, g_A) - Phi(V_B, g_B).
```

No other community term changes.

## Correctness claims

1. **Exactness.** Classify every boundary edge of `S`: an edge to the source
   remainder changes from internal to cut; an edge to `B` changes from cut to
   internal; an edge to any other community remains cut. Substitution in H2
   gives the implemented delta.
2. **Fixed-K preservation.** The target already exists and `|S| < |A|`, so
   neither a new community nor an empty source can occur.
3. **Monotonicity.** A move is accepted only when `Delta < -epsilon`; every
   accepted move strictly decreases exact H2 beyond the declared tolerance.
4. **Finite termination.** There are finitely many fixed-K assignments. Strict
   descent prevents revisiting one, so repeated node/block passes terminate.
5. **Local dominance.** If the proposal family contains every singleton,
   block-local optimality implies node-local optimality. The implementation
   certifies singleton and supplied-block neighborhoods separately and reports
   a joint certificate only after a complete no-improvement cycle.
6. **Cost.** Statistics take `O(sum_{v in S} degree(v))`; scoring all targets
   adds `O(K)`. Applying a move updates two summaries and `|S|` memberships.

The certificate is relative to the finite supplied proposal family. It is not a
claim of global optimality or a certificate over every vertex subset.

## Mechanical evidence

- `block_delta_100k_seed20260825.json`: 100,000 random weighted moves,
  including self-loops, compared with full objective reconstruction. Maximum
  absolute error: `6.217248937900877e-15` under a `1e-12` gate.
- `block_delta_exhaustive_n10.json`: all legal moves over every canonical K=2
  partition through `n=10` and every canonical K=3 partition through `n=8` on
  deterministic weighted graphs: 184,560 checks, maximum error
  `3.1086244689504383e-15`.
- `block_escape_witness_seed20260825.json`: a 10-node weighted graph whose
  partition has no improving legal singleton move but admits connected block
  `{1,3}: 1 -> 0` with exact delta `-0.07387266434510842`.

These establish implementation consistency and strict separation between
node-local and block-local search. They do not yet establish benchmark utility.
