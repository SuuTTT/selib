"""selib.seopt — a strong 2D structural-entropy minimizer (Louvain-style multilevel).

The naive `se_agglomerative` only ever *merges*; it cannot move a node out of a bad
early merge, so it gets stuck. This module does what Louvain does for modularity, but
for the **2D structural entropy** objective of Li & Pan (2016):

  H^2(P) = const(G)  +  sum_j  term(V_j, g_j)
  term(V, g) = (V/2m) log2 V  -  (g/2m) log2(V/2m)      (g>0; else just the first part)

where V_j = volume of community j, g_j = its cut, 2m = sum of degrees. `const(G)` is
partition-independent, so a single node move from community A to B only re-scores A and
B in O(deg(v)) time. We (1) sweep nodes, greedily moving each to the neighbour community
that most decreases H^2 (or to a fresh singleton), until no move helps; (2) contract each
community to a super-node — self-loop = internal weight, so the reduced graph has the
*same* H^2 algebra — and recurse; (3) multistart and keep the lowest-H^2 partition.

Correctness is checked in `__main__` against the canonical metric and exhaustive optima.
"""
from __future__ import annotations
import math
import networkx as nx

LOG2 = math.log(2.0)


def _term(V, g, two_m):
    if V <= 0:
        return 0.0
    t = (V / two_m) * (math.log(V) / LOG2)
    if g > 0:
        t -= (g / two_m) * (math.log(V / two_m) / LOG2)
    return t


def _const_within(deg, two_m):
    """Partition-independent part: -(1/2m) sum_v d_v log2 d_v."""
    s = 0.0
    for d in deg:
        if d > 0:
            s += d * (math.log(d) / LOG2)
    return -s / two_m


class _State:
    """Incremental 2D-SE state over a weighted graph with integer nodes 0..n-1.

    Tracks per-community volume V[c] and cut g[c] and the partition objective
    `obj = sum_j term(V_j, g_j)` (so absolute H^2 = const_within + obj)."""

    def __init__(self, n, adj, deg, sl, two_m, comm):
        self.n = n
        self.adj = adj          # adj[v] = dict {u: weight} for u != v
        self.deg = deg          # weighted degree (self-loop counted twice)
        self.sl = sl            # self-loop weight of v (0 for simple graphs)
        self.two_m = two_m
        self.comm = comm[:]     # node -> community id
        self.V = {}
        self.g = {}
        for v in range(n):
            c = self.comm[v]
            self.V[c] = self.V.get(c, 0.0) + deg[v]
        for v in range(n):
            for u, w in adj[v].items():
                if self.comm[u] != self.comm[v]:
                    self.g[self.comm[v]] = self.g.get(self.comm[v], 0.0) + w
        self.obj = sum(_term(self.V[c], self.g.get(c, 0.0), two_m) for c in self.V)

    def _w_to(self, v):
        """{community: total edge weight from v to *other* nodes in it}."""
        wt = {}
        for u, w in self.adj[v].items():
            c = self.comm[u]
            wt[c] = wt.get(c, 0.0) + w
        return wt

    def best_move(self, v, wt):
        """Return (target_comm, delta_obj) for the best move of v, or (None, 0)."""
        A = self.comm[v]
        dv, slv = self.deg[v], self.sl[v]
        VA, gA = self.V[A], self.g.get(A, 0.0)
        wvA = wt.get(A, 0.0)
        # remove v from A
        VA2 = VA - dv
        gA2 = gA - (dv - 2 * slv - wvA) + wvA           # = gA - dv + 2 slv + 2 wvA
        base = _term(VA, gA, self.two_m)
        removed = _term(VA2, gA2, self.two_m)
        best_t, best_d = A, 0.0                          # staying = no change
        candidates = set(wt.keys())
        candidates.add(-1)                               # -1 = fresh singleton
        for B in candidates:
            if B == A:
                continue
            VB = self.V.get(B, 0.0) if B != -1 else 0.0
            gB = self.g.get(B, 0.0) if B != -1 else 0.0
            wvB = wt.get(B, 0.0) if B != -1 else 0.0
            VB2 = VB + dv
            gB2 = gB + (dv - 2 * slv - wvB) - wvB        # = gB + dv - 2 slv - 2 wvB
            delta = (removed + _term(VB2, gB2, self.two_m)) - (base + _term(VB, gB, self.two_m))
            if delta < best_d - 1e-12:
                best_d, best_t = delta, B
        return best_t, best_d

    def apply(self, v, B, wt):
        A = self.comm[v]
        if B == A:
            return
        dv, slv = self.deg[v], self.sl[v]
        wvA = wt.get(A, 0.0)
        if B == -1:                                      # allocate a fresh id
            B = max(self.V.keys(), default=-1) + 1
            while B in self.V:
                B += 1
        wvB = wt.get(B, 0.0)
        VA, gA = self.V[A], self.g.get(A, 0.0)
        VB, gB = self.V.get(B, 0.0), self.g.get(B, 0.0)
        VA2 = VA - dv
        gA2 = gA - (dv - 2 * slv - wvA) + wvA
        VB2 = VB + dv
        gB2 = gB + (dv - 2 * slv - wvB) - wvB
        self.obj += (_term(VA2, gA2, self.two_m) - _term(VA, gA, self.two_m))
        self.obj += (_term(VB2, gB2, self.two_m) - _term(VB, gB, self.two_m))
        if VA2 <= 0:
            self.V.pop(A, None); self.g.pop(A, None)
        else:
            self.V[A] = VA2; self.g[A] = gA2
        self.V[B] = VB2; self.g[B] = gB2
        self.comm[v] = B


def _from_graph(G, comm=None):
    nodes = list(G.nodes())
    idx = {u: i for i, u in enumerate(nodes)}
    n = len(nodes)
    adj = [dict() for _ in range(n)]
    sl = [0.0] * n
    for u, v, w in G.edges(data="weight", default=1.0):
        a, b = idx[u], idx[v]
        if a == b:
            sl[a] += w
        else:
            adj[a][b] = adj[a].get(b, 0.0) + w
            adj[b][a] = adj[b].get(a, 0.0) + w
    deg = [sum(adj[v].values()) + 2 * sl[v] for v in range(n)]
    two_m = sum(deg)
    if comm is None:
        comm = list(range(n))
    return n, adj, deg, sl, two_m, comm, nodes


def _local_moves(state, order_rng, max_passes=30):
    n = state.n
    order = list(range(n))
    for _ in range(max_passes):
        order_rng.shuffle(order)
        moved = False
        for v in order:
            wt = state._w_to(v)
            B, delta = state.best_move(v, wt)
            if delta < -1e-12 and B != state.comm[v]:
                state.apply(v, B, wt)
                moved = True
        if not moved:
            break
    return state


def _relabel(comm):
    remap = {}
    return [remap.setdefault(c, len(remap)) for c in comm]


def _aggregate(adj, deg, sl, comm):
    """Contract communities -> super-nodes; return a networkx graph (with self-loops)."""
    lab = _relabel(comm)
    k = max(lab) + 1
    Gr = nx.Graph()
    Gr.add_nodes_from(range(k))
    w = {}
    self_w = [0.0] * k
    for v in range(len(adj)):
        cv = lab[v]
        self_w[cv] += sl[v]                       # carry original self-loops
        for u, wt in adj[v].items():
            cu = lab[u]
            if cu == cv:
                self_w[cv] += wt / 2.0            # internal edge counted once per endpoint
            elif cu > cv:
                w[(cv, cu)] = w.get((cv, cu), 0.0) + wt
    for (a, b), wt in w.items():
        Gr.add_edge(a, b, weight=wt)
    for c in range(k):
        if self_w[c] > 0:
            Gr.add_edge(c, c, weight=self_w[c])
    return Gr, lab


def louvain_se(G, seed=0, max_levels=20):
    """Free-k multilevel 2D-SE minimization. Returns labels aligned to list(G.nodes())."""
    import random
    rng = random.Random(seed)
    n, adj, deg, sl, two_m, comm, nodes = _from_graph(G)
    if two_m == 0:
        return [0] * n
    # node -> top-level community, refined level by level
    node_to_comm = list(range(n))
    cur_adj, cur_deg, cur_sl = adj, deg, sl
    cur_n = n
    for _ in range(max_levels):
        st = _State(cur_n, cur_adj, cur_deg, cur_sl, two_m, list(range(cur_n)))
        _local_moves(st, rng)
        lab = _relabel(st.comm)
        if max(lab) + 1 == cur_n:                 # no coarsening happened
            node_to_comm = [lab[c] for c in node_to_comm]
            break
        node_to_comm = [lab[c] for c in node_to_comm]
        Gr, _ = _aggregate(cur_adj, cur_deg, cur_sl, st.comm)
        cur_n, cur_adj, cur_deg, cur_sl, _, _, _ = _from_graph(Gr)
        if cur_n == 1:
            break
    return _relabel(node_to_comm)


def _merge_down_to_k(G, labels, k, seed=0):
    """Greedily merge whole communities (min 2D-SE increase) until exactly k remain."""
    n, adj, deg, sl, two_m, _, nodes = _from_graph(G)
    comm = list(labels)
    st = _State(n, adj, deg, sl, two_m, comm)
    # community adjacency (inter-community weight)
    cadj = {}
    for v in range(n):
        for u, w in adj[v].items():
            a, b = st.comm[v], st.comm[u]
            if a != b:
                key = (min(a, b), max(a, b))
                cadj[key] = cadj.get(key, 0.0) + w / 2.0  # each edge seen twice
    comms = set(st.comm)
    while len(comms) > k:
        best = None
        for (a, b), wab in cadj.items():
            if a not in comms or b not in comms:
                continue
            VA, gA = st.V[a], st.g.get(a, 0.0)
            VB, gB = st.V[b], st.g.get(b, 0.0)
            Vn = VA + VB
            gn = gA + gB - 2 * wab
            d = (_term(Vn, gn, two_m)) - (_term(VA, gA, two_m) + _term(VB, gB, two_m))
            if best is None or d < best[0]:
                best = (d, a, b, wab)
        if best is None:
            break
        _, a, b, wab = best
        # merge b into a
        st.V[a] = st.V[a] + st.V[b]
        st.g[a] = st.g.get(a, 0.0) + st.g.get(b, 0.0) - 2 * wab
        st.V.pop(b, None); st.g.pop(b, None)
        for v in range(n):
            if st.comm[v] == b:
                st.comm[v] = a
        comms.discard(b)
        new_cadj = {}
        for (x, y), w in cadj.items():
            x = a if x == b else x
            y = a if y == b else y
            if x == y:
                continue
            key = (min(x, y), max(x, y))
            new_cadj[key] = new_cadj.get(key, 0.0) + w
        cadj = new_cadj
    return _relabel(st.comm)


def se_optimize(G, k=None, seed=0, starts=8):
    """Best 2D-SE partition via multistart multilevel Louvain-SE.

    If `k` is given and the free-k result has more than k communities, greedily
    merge down to k (cannot fabricate splits, so fewer-than-k is returned as is).
    Labels are aligned to list(G.nodes())."""
    import random
    best_labels, best_obj = None, float("inf")
    for s in range(starts):
        lab = louvain_se(G, seed=seed * 1000 + s)
        # exact objective for selection
        n, adj, deg, sl, two_m, _, _ = _from_graph(G)
        st = _State(n, adj, deg, sl, two_m, lab)
        if st.obj < best_obj - 1e-12:
            best_obj, best_labels = st.obj, lab
    if best_labels is None:
        best_labels = [0] * G.number_of_nodes()
    if k is not None and len(set(best_labels)) > k:
        best_labels = _merge_down_to_k(G, best_labels, k, seed=seed)
    return best_labels


# ----------------------------- self-tests -----------------------------------
def _exact_min_se(G):
    """Brute-force minimum 2D-SE over all set partitions (n <= ~9). For validation."""
    from . import metrics as M
    n = G.number_of_nodes()
    best = (float("inf"), None)
    # restricted-growth strings enumerate all set partitions
    a = [0] * n
    def rec(i, mx):
        nonlocal best
        if i == n:
            h = M.structural_entropy_2d(G, a[:])
            if h < best[0]:
                best = (h, a[:])
            return
        for c in range(mx + 1):
            a[i] = c
            rec(i + 1, max(mx, c) + (1 if c == mx else 0))
    rec(0, 0)
    return best


def _selftest():
    import random
    from . import metrics as M
    random.seed(0)
    print("== consistency: const_within + sum term(j) == metric ==")
    for gi, G in enumerate([nx.karate_club_graph(),
                            nx.gnp_random_graph(12, 0.3, seed=1),
                            nx.barbell_graph(5, 1)]):
        G = nx.convert_node_labels_to_integers(G)
        n, adj, deg, sl, two_m, _, _ = _from_graph(G)
        lab = [random.randrange(3) for _ in range(n)]
        st = _State(n, adj, deg, sl, two_m, lab)
        recomputed = _const_within(deg, two_m) + st.obj
        canonical = M.structural_entropy_2d(G, lab)
        ok = abs(recomputed - canonical) < 1e-9
        print(f"  graph{gi}: incr={recomputed:.6f} metric={canonical:.6f} {'OK' if ok else 'MISMATCH'}")
        assert ok

    print("== delta consistency over random moves ==")
    G = nx.convert_node_labels_to_integers(nx.gnp_random_graph(15, 0.3, seed=2))
    n, adj, deg, sl, two_m, _, _ = _from_graph(G)
    st = _State(n, adj, deg, sl, two_m, list(range(n)))
    applied = 0
    for _ in range(400):
        v = random.randrange(n)
        wt = st._w_to(v)
        # exercise deltas for ALL candidate targets, not just the best
        A = st.comm[v]
        for B in list(wt.keys()) + [-1]:
            if B == A:
                continue
            _, d_best = st.best_move(v, wt)  # consistency of scorer
            # compute this specific candidate's delta the same way apply will
            VA, gA = st.V[A], st.g.get(A, 0.0)
            VB = st.V.get(B, 0.0) if B != -1 else 0.0
            gB = st.g.get(B, 0.0) if B != -1 else 0.0
            wvA, wvB = wt.get(A, 0.0), (wt.get(B, 0.0) if B != -1 else 0.0)
            slv = st.sl[v]; dv = st.deg[v]
            VA2 = VA - dv; gA2 = gA - (dv - 2 * slv - wvA) + wvA
            VB2 = VB + dv; gB2 = gB + (dv - 2 * slv - wvB) - wvB
            cand_delta = (_term(VA2, gA2, two_m) + _term(VB2, gB2, two_m)) \
                - (_term(VA, gA, two_m) + _term(VB, gB, two_m))
            assert d_best <= cand_delta + 1e-9, (d_best, cand_delta)
        B, delta = st.best_move(v, wt)
        if B == A:
            continue
        before = st.obj
        st.apply(v, B, wt)
        st2 = _State(n, adj, deg, sl, two_m, st.comm)   # ground-truth recompute
        assert abs(st2.obj - st.obj) < 1e-7, (st2.obj, st.obj)
        assert abs((st.obj - before) - delta) < 1e-7, (st.obj - before, delta)
        applied += 1
    print(f"  {applied} real moves: incremental obj == full recompute, best<=all-candidates  OK")

    print("== vs exhaustive optimum (small graphs) ==")
    for gi, G in enumerate([nx.gnp_random_graph(8, 0.4, seed=3),
                            nx.path_graph(7), nx.cycle_graph(8),
                            nx.barbell_graph(3, 0)]):
        G = nx.convert_node_labels_to_integers(G)
        opt, _ = _exact_min_se(G)
        got = M.structural_entropy_2d(G, se_optimize(G, starts=12))
        gap = got - opt
        print(f"  graph{gi}: optimizer={got:.6f} exact_opt={opt:.6f} gap={gap:+.6f}"
              f" {'OPTIMAL' if gap < 1e-6 else 'near' if gap < 0.02 else 'SUBOPTIMAL'}")
    print("== compare to naive agglomerative on Karate ==")
    from .se import se_agglomerative
    from scipy.cluster.hierarchy import fcluster
    G = nx.convert_node_labels_to_integers(nx.karate_club_graph())
    Z = se_agglomerative(G)
    for k in (2, 3, 4):
        lab_ag = list(fcluster(Z, t=k, criterion="maxclust"))
        h_ag = M.structural_entropy_2d(G, lab_ag)
        print(f"  agglomerative k={k}: H2={h_ag:.6f}")
    lab_opt = se_optimize(G)
    print(f"  se_optimize free-k ({len(set(lab_opt))} comms): H2={M.structural_entropy_2d(G, lab_opt):.6f}")
    print("ALL SELFTESTS PASSED")


if __name__ == "__main__":
    _selftest()


# --------------------- K-constrained SE clustering ---------------------------
# Port of `constrained_k_multistart` (SuuTTT/se-label-alignment, seclust-targetk
# "SE-HybridK", idea 2.1'): multistart local search constrained to exactly K
# clusters. Each restart starts from a random (or spectral) K-partition and
# runs local moves that can neither create clusters nor empty one - so the
# optimizer never visits the over-fragmented free-k minimum it would otherwise
# have to merge down from. Addresses SE's over-resolution at free k.

def _spectral_seed_labels(G, k, seed=0):
    """Top-k normalized-Laplacian eigenvectors + tiny Lloyd k-means (numpy only)."""
    import numpy as _np
    nodes = list(G.nodes())
    n = len(nodes)
    idx = {u: i for i, u in enumerate(nodes)}
    A = _np.zeros((n, n))
    for u, v, d in G.edges(data=True):
        w = d.get("weight", 1.0)
        A[idx[u], idx[v]] = A[idx[v], idx[u]] = w
    deg = A.sum(1)
    reg = 0.5 * deg.mean()                      # regularized Laplacian (HybridK recipe)
    dinv = 1.0 / _np.sqrt(deg + reg)
    L = _np.eye(n) - dinv[:, None] * A * dinv[None, :]
    vals, vecs = _np.linalg.eigh(L)
    X = vecs[:, :k]
    X /= _np.linalg.norm(X, axis=1, keepdims=True).clip(min=1e-12)
    rng = _np.random.default_rng(seed)
    C = X[rng.permutation(n)[:k]].copy()
    for _ in range(25):
        d2 = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        lab = d2.argmin(1)
        for j in range(k):
            m = lab == j
            if m.any():
                C[j] = X[m].mean(0)
    # ensure exactly k non-empty clusters
    for j in range(k):
        if not (lab == j).any():
            lab[rng.integers(0, n)] = j
    return list(lab)


def _local_moves_fixed_k(state, order_rng, max_passes=20):
    """Local moves restricted to existing communities; never empties a source."""
    n = state.n
    members = {}
    for v in range(n):
        members[state.comm[v]] = members.get(state.comm[v], 0) + 1
    order = list(range(n))
    for _ in range(max_passes):
        order_rng.shuffle(order)
        moved = False
        for v in order:
            A = state.comm[v]
            if members[A] <= 1:
                continue                          # moving v would empty A
            wt = state._w_to(v)
            # constrained best move: existing communities only (no -1)
            dv, slv = state.deg[v], state.sl[v]
            VA, gA = state.V[A], state.g.get(A, 0.0)
            wvA = wt.get(A, 0.0)
            VA2 = VA - dv
            gA2 = gA - (dv - 2 * slv - wvA) + wvA
            base = _term(VA, gA, state.two_m)
            removed = _term(VA2, gA2, state.two_m)
            best_t, best_d = A, 0.0
            for B in state.V:
                if B == A:
                    continue
                VB, gB = state.V[B], state.g.get(B, 0.0)
                wvB = wt.get(B, 0.0)
                VB2 = VB + dv
                gB2 = gB + (dv - 2 * slv - wvB) - wvB
                delta = (removed + _term(VB2, gB2, state.two_m)) - (base + _term(VB, gB, state.two_m))
                if delta < best_d - 1e-12:
                    best_d, best_t = delta, B
            if best_t != A:
                state.apply(v, best_t, wt)
                members[A] -= 1
                members[best_t] = members.get(best_t, 0) + 1
                moved = True
        if not moved:
            break
    return state


def se_optimize_fixed_k(G, k, starts=8, max_passes=20, seed=0, spectral_init=True):
    """Best 2D-SE partition with EXACTLY k communities (multistart local search).

    Unlike se_optimize(G, k=...) - which minimizes at free k then greedily
    merges down - this never leaves the K-cluster subspace, avoiding SE's
    over-resolution. Labels aligned to list(G.nodes())."""
    import random as _random
    n, adj, deg, sl, two_m, _, _ = _from_graph(G)
    if k < 1 or k > n:
        raise ValueError("k out of range")
    rng = _random.Random(seed)
    nrng = __import__("numpy").random.default_rng(seed)

    def balanced_random():
        lab = list(nrng.integers(0, k, size=n))
        seeds = list(nrng.permutation(n)[:k])
        for j, v in enumerate(seeds):
            lab[v] = j
        return [int(x) for x in lab]

    inits = []
    if spectral_init and k >= 2 and n <= 3000:
        try:
            inits.append([int(x) for x in _spectral_seed_labels(G, k, seed=seed)])
        except Exception:
            pass
    while len(inits) < starts:
        inits.append(balanced_random())

    best_lab, best_obj = None, float("inf")
    for i, init in enumerate(inits):
        st = _State(n, adj, deg, sl, two_m, init)
        _local_moves_fixed_k(st, _random.Random(seed * 997 + i), max_passes)
        if st.obj < best_obj - 1e-12:
            best_obj, best_lab = st.obj, st.comm[:]
    return _relabel(best_lab)
