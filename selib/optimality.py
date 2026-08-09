"""Exact small-graph certificates for encoding-tree structural entropy.

The subset dynamic program is exponential and is intended for verification,
not as a replacement for scalable hierarchy constructors such as NEST.
"""
from __future__ import annotations

import math

from .htree import TNode, _graph_arrays, annotate, hd_se


def exact_tree_entropy(graph, max_nodes=18, return_tree=False):
    """Return the globally minimum encoding-tree entropy for a small graph.

    Any multiway encoding tree can be refined to a binary tree without
    increasing structural entropy.  It is therefore sufficient to optimize
    over unordered binary splits.  The recurrence uses ``O(3**n)`` time and
    ``O(2**n)`` memory, so ``max_nodes`` is an explicit safety guard.

    When ``return_tree`` is true, the returned tree uses the integer vertex
    order produced by :func:`_graph_arrays` (0 through n-1).
    """
    _, _, n, adj, deg, total_volume = _graph_arrays(graph)
    if n == 0 or total_volume <= 0:
        result = (0.0, None) if return_tree else 0.0
        return result
    if n > max_nodes:
        raise ValueError(
            f"exact optimization requested for n={n}; safety limit is {max_nodes}"
        )

    count = 1 << n
    volume = [0.0] * count
    internal_weight = [0.0] * count
    boundary = [0.0] * count

    for mask in range(1, count):
        bit = mask & -mask
        vertex = bit.bit_length() - 1
        rest = mask ^ bit
        volume[mask] = volume[rest] + deg[vertex]
        added = 0.0
        scan = rest
        while scan:
            neighbor_bit = scan & -scan
            neighbor = neighbor_bit.bit_length() - 1
            added += adj[vertex].get(neighbor, 0.0)
            scan ^= neighbor_bit
        internal_weight[mask] = internal_weight[rest] + added
        cut = volume[mask] - 2.0 * internal_weight[mask]
        boundary[mask] = 0.0 if abs(cut) < 1e-12 else cut

    optimum = [math.inf] * count
    split = [0] * count
    for vertex in range(n):
        optimum[1 << vertex] = 0.0

    for mask in range(1, count):
        if mask & (mask - 1) == 0:
            continue
        anchor = mask & -mask
        left = (mask - 1) & mask
        while left:
            if left & anchor:
                right = mask ^ left
                if right:
                    contribution = 0.0
                    if boundary[left] > 0 and volume[left] > 0:
                        contribution -= (
                            boundary[left] / total_volume
                            * math.log2(volume[left] / volume[mask])
                        )
                    if boundary[right] > 0 and volume[right] > 0:
                        contribution -= (
                            boundary[right] / total_volume
                            * math.log2(volume[right] / volume[mask])
                        )
                    candidate = optimum[left] + optimum[right] + contribution
                    if candidate < optimum[mask] - 1e-15:
                        optimum[mask] = candidate
                        split[mask] = left
            left = (left - 1) & mask

    full = count - 1
    if not return_tree:
        return float(optimum[full])

    def build(mask):
        if mask & (mask - 1) == 0:
            return TNode(vertex=mask.bit_length() - 1)
        left = split[mask]
        return TNode(children=[build(left), build(mask ^ left)])

    root = build(full)
    annotate(root, deg, adj, total_volume)
    observed = hd_se(root, total_volume)
    if abs(observed - optimum[full]) > 1e-9:
        raise AssertionError(
            f"dynamic-program value {optimum[full]} != rebuilt tree {observed}"
        )
    return float(optimum[full]), root


def edge_lca_lower_bound(graph):
    """Computable lower bound on the entropy of every encoding tree.

    For an edge uv, the LCA module has volume at least d_u+d_v.  Substituting
    this minimum into the edge-LCA form of structural entropy yields the bound.
    Self-loops are ignored because they never cross an encoding-tree module.
    """
    nodes, index, _, _, deg, total_volume = _graph_arrays(graph)
    if total_volume <= 0:
        return 0.0
    bound = 0.0
    for u, v, weight in graph.edges(data="weight", default=1.0):
        if u == v or weight <= 0:
            continue
        du, dv = deg[index[u]], deg[index[v]]
        if du <= 0 or dv <= 0:
            continue
        bound += (weight / total_volume) * math.log2(
            ((du + dv) ** 2) / (du * dv)
        )
    return float(bound)
