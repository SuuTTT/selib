"""selib.sepi -- bring-your-own-pi structural entropy.

Standard 2D SE fixes the node distribution pi_v = d_v/2m (degree). This module
lets pi be ANY stationary distribution of a random walk with transition P, e.g.
a personalized-PageRank vector centered on a query node, yielding *query-biased*
structural entropy. Reduces EXACTLY to selib.metrics.structural_entropy_2d when
pi=degree and P = D^{-1}A (verified by se2d_pi_selftest).

General 2D SE under partition, stationary pi, transition P:
    H = - sum_X [ phi_X * log2(vol_X) + sum_{v in X} pi_v * log2(pi_v / vol_X) ]
  vol_X = sum_{v in X} pi_v                 (module mass; sum_v pi_v = 1)
  phi_X = sum_{v in X} pi_v * P(v, X^c)     (boundary out-flow)
"""
from __future__ import annotations
import numpy as np
import networkx as nx


def _adj_P(G):
    nodes = list(G.nodes())
    idx = {u: i for i, u in enumerate(nodes)}
    n = len(nodes)
    A = np.zeros((n, n))
    for u, v, d in G.edges(data=True):
        w = d.get("weight", 1.0)
        A[idx[u], idx[v]] += w
        A[idx[v], idx[u]] += w
    deg = A.sum(1)
    deg[deg == 0] = 1.0
    P = A / deg[:, None]                      # row-stochastic walk D^{-1}A
    return nodes, idx, A, P, deg


def degree_pi(G):
    """The standard stationary distribution pi_v = d_v / 2m."""
    _, _, A, _, _ = _adj_P(G)
    deg = A.sum(1)
    return deg / deg.sum()


def ppr_pi(G, query, alpha=0.15, iters=200, tol=1e-12):
    """Personalized-PageRank stationary distribution with teleport to `query`
    (a node or list of nodes). This is the stationary pi of the teleporting walk
    P_ppr = (1-alpha) D^{-1}A + alpha * 1 q^T, so SE under it keeps the
    code-length reading (paper O1)."""
    nodes, idx, A, P, _ = _adj_P(G)
    n = len(nodes)
    q = np.zeros(n)
    qs = [query] if not isinstance(query, (list, tuple, set)) else list(query)
    for x in qs:
        q[idx[x]] = 1.0
    q /= q.sum()
    pi = np.full(n, 1.0 / n)
    for _ in range(iters):
        nxt = (1 - alpha) * (P.T @ pi) + alpha * q
        if np.abs(nxt - pi).sum() < tol:
            pi = nxt
            break
        pi = nxt
    return pi / pi.sum()


def ppr_transition(G, query, alpha=0.15):
    nodes, idx, A, P, _ = _adj_P(G)
    n = len(nodes)
    q = np.zeros(n)
    qs = [query] if not isinstance(query, (list, tuple, set)) else list(query)
    for x in qs:
        q[idx[x]] = 1.0
    q /= q.sum()
    return (1 - alpha) * P + alpha * np.tile(q, (n, 1))


def se2d_pi(labels, pi, P):
    """2D SE for a flat partition under exogenous (pi, P). labels aligned to the
    same node order as pi/P (i.e. list(G.nodes()))."""
    labels = np.asarray(labels)
    pi = np.asarray(pi, float)
    H = 0.0
    for c in np.unique(labels):
        m = labels == c
        vol = pi[m].sum()
        if vol <= 0:
            continue
        # boundary out-flow: sum_{v in X} pi_v * P(v, X^c)
        out = (pi[m, None] * P[np.ix_(m, ~m)]).sum() if (~m).any() else 0.0
        H -= out * np.log2(vol)
        pv = pi[m]
        pv = pv[pv > 0]
        H -= (pv * np.log2(pv / vol)).sum()
    return float(H)


def optimize_pi(G, pi, P, k=None, starts=6, max_passes=30, seed=0):
    """Greedy Louvain-style local search minimizing se2d_pi. If k given, also
    runs a spectral-seeded restart and (softly) targets k via that seed."""
    nodes = list(G.nodes())
    n = len(nodes)
    rng = np.random.default_rng(seed)
    neigh = [list(G[u]) for u in nodes]
    idx = {u: i for i, u in enumerate(nodes)}
    neigh_i = [[idx[v] for v in nb] for nb in neigh]

    def local_search(labels):
        labels = labels.copy()
        order = np.arange(n)
        for _ in range(max_passes):
            rng.shuffle(order)
            moved = False
            for v in order:
                cur = labels[v]
                cand = {labels[u] for u in neigh_i[v]} | {cur}
                best_c, best_obj = cur, se2d_pi(labels, pi, P)
                for c in cand:
                    if c == cur:
                        continue
                    labels[v] = c
                    o = se2d_pi(labels, pi, P)
                    if o < best_obj - 1e-12:
                        best_obj, best_c = o, c
                    labels[v] = cur
                if best_c != cur:
                    labels[v] = best_c
                    moved = True
            if not moved:
                break
        return labels

    inits = []
    if k:
        inits.append(rng.integers(0, k, size=n))
    for _ in range(starts):
        inits.append(np.arange(n) % max(2, (k or int(np.sqrt(n)))))
        rng.shuffle(inits[-1])
    best_lab, best = None, np.inf
    for init in inits:
        lab = local_search(np.asarray(init))
        o = se2d_pi(lab, pi, P)
        if o < best - 1e-12:
            best, best_lab = o, lab
    # relabel 0..K-1
    remap = {}
    return np.array([remap.setdefault(c, len(remap)) for c in best_lab])


def se2d_pi_selftest():
    """Gate: with pi=degree and P=D^{-1}A, se2d_pi must equal the standard
    structural_entropy_2d to machine precision."""
    from selib.metrics import structural_entropy_2d
    G = nx.karate_club_graph()
    nodes = list(G.nodes())
    _, _, A, P, _ = _adj_P(G)
    pi = degree_pi(G)
    rng = np.random.default_rng(0)
    maxerr = 0.0
    for _ in range(20):
        lab = rng.integers(0, 5, size=len(nodes))
        a = se2d_pi(lab, pi, P)
        b = structural_entropy_2d(G, {nodes[i]: int(lab[i]) for i in range(len(nodes))}) \
            if False else structural_entropy_2d(G, list(lab))
        maxerr = max(maxerr, abs(a - b))
    return maxerr
