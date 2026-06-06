"""selib.se — native structural-entropy core (seed of the encoding-tree + SE core).

Provides the SE-agglomerative encoding tree and Dasgupta cost. 2D structural
entropy lives in selib.metrics. This module is the native, dependency-light core
that the rest of selib (and external method wrappers) build on.
"""
from __future__ import annotations
import math
import numpy as np
import networkx as nx


def se_agglomerative(G):
    """Greedy agglomerative minimizing 2D structural entropy. Returns scipy-style
    linkage Z (n-1 x 4). Clusters keyed 0..n-1 (leaves) then n.. (merges)."""
    nodes = list(G.nodes()); n = len(nodes); idx = {u: i for i, u in enumerate(nodes)}
    deg = np.array([G.degree(u, weight="weight") for u in nodes], dtype=float)
    m2 = deg.sum()
    if m2 == 0:
        m2 = 1.0
    # cluster state
    V = {i: deg[i] for i in range(n)}            # volume
    g = {i: deg[i] for i in range(n)}            # cut (singleton: all edges leave)
    members = {i: [i] for i in range(n)}
    cid = {i: i for i in range(n)}               # current cluster id of leaf
    w = {}                                       # cross weight between clusters
    for u, v, wt in G.edges(data="weight", default=1.0):
        a, b = idx[u], idx[v]
        if a == b:
            continue
        key = (min(a, b), max(a, b)); w[key] = w.get(key, 0.0) + wt
    adj = {i: {} for i in range(n)}
    for (a, b), wt in w.items():
        adj[a][b] = wt; adj[b][a] = wt

    def plog(x):
        return x * math.log2(x) if x > 0 else 0.0

    def delta(a, b, wab):
        # SE change from merging clusters a, b. Every log2 is guarded against a
        # zero-volume cluster (isolated nodes / disconnected components): the limit
        # of V*log2(.../V) as V->0 is 0, so a volume-0 cluster contributes nothing.
        Va, Vb, Vab = V[a], V[b], V[a] + V[b]
        ga, gb = g[a], g[b]; gab = ga + gb - 2 * wab
        dW = 0.0
        if Va > 0 and Vab > 0:
            dW += (Va / m2) * math.log2(Vab / Va)
        if Vb > 0 and Vab > 0:
            dW += (Vb / m2) * math.log2(Vab / Vb)
        dM = 0.0
        if Vab > 0:
            dM -= (gab / m2) * math.log2(Vab / m2)
            if Va > 0:
                dM += (ga / m2) * math.log2(Va / m2)
            if Vb > 0:
                dM += (gb / m2) * math.log2(Vb / m2)
        return dW + dM

    Z = []; next_id = n; node_id = {i: i for i in range(n)}; size = {i: 1 for i in range(n)}
    alive = set(range(n))
    for _ in range(n - 1):
        best = None
        for a in alive:
            for b, wab in adj[a].items():
                if b > a and b in alive:
                    d = delta(a, b, wab)
                    if best is None or d < best[0]:
                        best = (d, a, b, wab)
        if best is None:  # disconnected: merge any two
            it = list(alive); a, b, wab = it[0], it[1], 0.0; d = delta(a, b, 0.0); best = (d, a, b, wab)
        d, a, b, wab = best
        # merge b into a
        Vab = V[a] + V[b]; gab = g[a] + g[b] - 2 * wab
        Z.append([node_id[a], node_id[b], max(d, 0) + len(Z) * 1e-9, size[a] + size[b]])
        V[a] = Vab; g[a] = gab; size[a] = size[a] + size[b]; node_id[a] = next_id
        # merge adjacency
        for c, wbc in list(adj[b].items()):
            if c == a:
                continue
            adj[a][c] = adj[a].get(c, 0.0) + wbc; adj[c][a] = adj[c].get(a, 0.0) + wbc
            adj[c].pop(b, None)
        adj.pop(b, None); adj[a].pop(b, None)
        alive.discard(b); next_id += 1
    return np.array(Z, dtype=float)



def dasgupta_cost(G, Z):
    """Dasgupta cost of binary dendrogram Z on weighted graph G. Lower better.
    cost = sum_{(i,j) in E} w_ij * |leaves under LCA(i,j)|."""
    nodes = list(G.nodes()); n = len(nodes); idx = {u: i for i, u in enumerate(nodes)}
    # build tree: cluster id -> (children, leafset size); leaves 0..n-1
    children = {}; leafcount = {i: 1 for i in range(n)}
    nid = n
    for a, b, _, sz in Z:
        children[nid] = (int(a), int(b)); leafcount[nid] = int(sz); nid += 1
    root = nid - 1
    # leaf -> path to root (ancestor list). Compute LCA via ancestor sets.
    parent = {}
    for c, (a, b) in children.items():
        parent[a] = c; parent[b] = c
    def ancestors(x):
        anc = [];
        while x in parent:
            x = parent[x]; anc.append(x)
        return anc
    anc_cache = {i: ancestors(i) for i in range(n)}
    cost = 0.0
    for u, v, wt in G.edges(data="weight", default=1.0):
        i, j = idx[u], idx[v]
        if i == j:
            continue
        av = set(anc_cache[i])
        lca = next((a for a in anc_cache[j] if a in av), root)
        cost += wt * leafcount.get(lca, n)
    return cost

