"""Metrics for the SE benchmark.

Two kinds:
  (1) external accuracy vs. ground truth: ARI, NMI (disjoint).
  (2) cross-objective values of a partition: modularity, two-level map-equation
      codelength, and 2D structural entropy. These let us answer R2's
      "comparison with other graph metrics": for each method's output we report
      what every objective thinks of it, exposing where the objectives agree and
      disagree.

All objective definitions follow the canonical sources:
  - 2D structural entropy: Li & Pan, "Structural information and dynamical
    complexity of networks", IEEE TIT 2016.
  - map equation (two-level): Rosvall & Bergstrom, PNAS 2008.
  - modularity: Newman 2004 (via networkx).
Undirected, unweighted-or-weighted graphs; weights via 'weight' edge attr.
"""
from __future__ import annotations
import math
import numpy as np
import networkx as nx
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score


# ---- (1) external accuracy --------------------------------------------------
def ari(true_labels, pred_labels) -> float:
    return float(adjusted_rand_score(true_labels, pred_labels))


def nmi(true_labels, pred_labels) -> float:
    return float(normalized_mutual_info_score(true_labels, pred_labels))


def _labels_to_partition(labels) -> list[set]:
    groups: dict = {}
    for node, lab in enumerate(labels):
        groups.setdefault(lab, set()).add(node)
    return list(groups.values())


# ---- (2) cross-objective values --------------------------------------------
def modularity(G: nx.Graph, labels) -> float:
    """Newman modularity of the given node->label assignment (index-aligned)."""
    comm = _labels_to_partition([labels[n] for n in range(G.number_of_nodes())])
    # map set-of-index to set-of-node using sorted node order
    nodes = list(G.nodes())
    comm_nodes = [set(nodes[i] for i in c) for c in comm]
    return float(nx.community.modularity(G, comm_nodes, weight="weight"))


def structural_entropy_2d(G: nx.Graph, labels) -> float:
    """2D structural entropy (bits) of a graph under a flat partition.

    H^2 = - sum_j sum_{v in V_j} (d_v/2m) log2(d_v/V_j)
          - sum_j (g_j/2m) log2(V_j/2m)
    where V_j = volume(module j) = sum of degrees in j, g_j = cut of module j,
    2m = sum of degrees, d_v = degree(v). Lower = better hierarchy fit.
    """
    nodes = list(G.nodes())
    idx = {n: i for i, n in enumerate(nodes)}
    deg = dict(G.degree(weight="weight"))
    two_m = sum(deg.values())
    if two_m == 0:
        return 0.0
    # module bookkeeping
    mod_of = {n: labels[idx[n]] for n in nodes}
    vol: dict = {}
    for n in nodes:
        vol[mod_of[n]] = vol.get(mod_of[n], 0.0) + deg[n]
    cut: dict = {}  # g_j: weight of edges leaving module j
    for u, v, w in G.edges(data="weight", default=1.0):
        if mod_of[u] != mod_of[v]:
            cut[mod_of[u]] = cut.get(mod_of[u], 0.0) + w
            cut[mod_of[v]] = cut.get(mod_of[v], 0.0) + w
    H = 0.0
    for n in nodes:
        dv, Vj = deg[n], vol[mod_of[n]]
        if dv > 0 and Vj > 0:
            H -= (dv / two_m) * math.log2(dv / Vj)
    for j, Vj in vol.items():
        gj = cut.get(j, 0.0)
        if gj > 0 and Vj > 0:
            H -= (gj / two_m) * math.log2(Vj / two_m)
    return float(H)


def map_equation_codelength(G: nx.Graph, labels) -> float:
    """Two-level map equation codelength L(M) in bits (undirected approx via
    degree-proportional stationary distribution)."""
    nodes = list(G.nodes())
    idx = {n: i for i, n in enumerate(nodes)}
    deg = dict(G.degree(weight="weight"))
    two_m = sum(deg.values())
    if two_m == 0:
        return 0.0
    p = {n: deg[n] / two_m for n in nodes}            # node visit rates
    mod_of = {n: labels[idx[n]] for n in nodes}
    mods = set(mod_of.values())
    # exit prob of each module q_i = (cut_i)/2m
    cut: dict = {m: 0.0 for m in mods}
    for u, v, w in G.edges(data="weight", default=1.0):
        if mod_of[u] != mod_of[v]:
            cut[mod_of[u]] += w
            cut[mod_of[v]] += w
    q = {m: cut[m] / two_m for m in mods}
    p_mod = {m: 0.0 for m in mods}
    for n in nodes:
        p_mod[mod_of[n]] += p[n]
    q_sum = sum(q.values())

    def plogp(x):
        return x * math.log2(x) if x > 0 else 0.0

    # Rosvall-Bergstrom two-level map equation L(M) in bits:
    # L = q_sum*log(q_sum) - 2*sum_i q_i*log(q_i) - sum_a p_a*log(p_a)
    #     + sum_i (q_i + sum_{a in i} p_a) * log(q_i + sum_{a in i} p_a)
    L = plogp(q_sum)
    L -= 2 * sum(plogp(q[m]) for m in mods)
    L -= sum(plogp(p[n]) for n in nodes)
    L += sum(plogp(q[m] + p_mod[m]) for m in mods)
    return float(L)


def cross_objective(G: nx.Graph, labels) -> dict[str, float]:
    return {
        "modularity": modularity(G, labels),
        "map_equation": map_equation_codelength(G, labels),
        "structural_entropy_2d": structural_entropy_2d(G, labels),
        "num_communities": int(len(set(labels))),
    }
