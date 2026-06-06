"""selib.calc — a standard structural-entropy calculator.

One front door for *computing* structural entropy, separate from the optimizers:

    selib.structural_entropy(G)              # optimal 2D-SE (minimized over partitions)
    selib.structural_entropy(G, labels)      # 2D-SE of a given partition
    selib.structural_entropy(G, dim=1)       # 1D-SE (positioning entropy, partition-free)
    selib.structural_entropy(G, tree=root)   # encoding-tree entropy H^T of a given tree
    selib.se_report(G)                       # {1d, 2d-optimal, tree-optimal, k, ...}

All quantities are in bits and follow Li & Pan (2016). Two invariants the
self-test checks: the 2D-SE of either trivial partition (all-singletons or
one-community) equals the 1D-SE, and the optimal 2D-SE is <= the 1D-SE.
"""
from __future__ import annotations
import math
import networkx as nx
from . import metrics as M


def one_dimensional(G) -> float:
    """1D structural entropy H^1(G) = -sum_v (d_v/2m) log2(d_v/2m). The entropy of
    the stationary random walk with no partition (an upper bound on all H^k)."""
    deg = dict(G.degree(weight="weight"))
    two_m = sum(deg.values())
    if two_m <= 0:
        return 0.0
    return float(-sum((d / two_m) * math.log2(d / two_m) for d in deg.values() if d > 0))


def two_dimensional(G, labels) -> float:
    """2D structural entropy of a flat partition (labels aligned to list(G.nodes()))."""
    return M.structural_entropy_2d(G, labels)


def tree_entropy(G, tree) -> float:
    """Structural entropy of an encoding tree (a selib htree.TNode) over G."""
    from .htree import annotate, hd_se, _graph_arrays
    _, _, _, adj, deg, vol = _graph_arrays(G)
    annotate(tree, deg, adj, vol)
    return float(hd_se(tree, vol))


def optimal_2d(G, k=None, seed=0):
    """SE-optimal flat partition (minimizes 2D-SE) via se_louvain.
    Returns (labels, H^2). With k set, the result is merged down to k communities."""
    from .seopt import se_optimize
    labels = se_optimize(G, k=k, seed=seed)
    return labels, two_dimensional(G, labels)


def optimal_tree(G, seed=0):
    """SE-optimal encoding tree via se_hier. Returns (tree, H^T)."""
    from .htree import encoding_tree, hd_se
    root, _, _, vol = encoding_tree(G, seed=seed)
    return root, float(hd_se(root, vol))


def structural_entropy(G, partition=None, *, dim=2, tree=None, k=None):
    """Unified entry point. See module docstring for the call forms."""
    if tree is not None:
        return tree_entropy(G, tree)
    if dim == 1:
        return one_dimensional(G)
    if dim == 2:
        if partition is None:
            return optimal_2d(G, k=k)[1]
        return two_dimensional(G, partition)
    raise ValueError("dim must be 1 or 2 (or pass tree=...)")


def se_report(G, k=None) -> dict:
    """A one-call summary: graph size, 1D-SE, optimal 2D-SE (+#communities), and
    optimal encoding-tree entropy. Every value computed, none assumed."""
    labels, se2 = optimal_2d(G, k=k)
    _, hT = optimal_tree(G)
    h1 = one_dimensional(G)
    return {
        "n": G.number_of_nodes(),
        "m": G.number_of_edges(),
        "se_1d": round(h1, 6),
        "se_2d_optimal": round(se2, 6),
        "num_communities": int(len(set(labels))),
        "se_tree_optimal": round(hT, 6),
        "compression_2d": round((h1 - se2) / h1, 4) if h1 > 0 else 0.0,
    }


def _selftest():
    import random
    random.seed(0)
    print("== 2D-SE of trivial partitions == 1D-SE; optimal <= 1D ==")
    for gi, G in enumerate([nx.karate_club_graph(),
                            nx.les_miserables_graph(),
                            nx.gnp_random_graph(40, 0.2, seed=1)]):
        G = nx.convert_node_labels_to_integers(G)
        n = G.number_of_nodes()
        h1 = one_dimensional(G)
        singletons = list(range(n))
        one_comm = [0] * n
        s_se = two_dimensional(G, singletons)
        o_se = two_dimensional(G, one_comm)
        opt = optimal_2d(G)[1]
        ok = abs(s_se - h1) < 1e-9 and abs(o_se - h1) < 1e-9 and opt <= h1 + 1e-9
        print(f"  graph{gi}: 1D={h1:.4f} singletons={s_se:.4f} one-comm={o_se:.4f} "
              f"optimal={opt:.4f} {'OK' if ok else 'FAIL'}")
        assert ok
    print("== se_report ==")
    print(" ", se_report(nx.convert_node_labels_to_integers(nx.karate_club_graph())))
    print("ALL CALC SELFTESTS PASSED")


if __name__ == "__main__":
    _selftest()
