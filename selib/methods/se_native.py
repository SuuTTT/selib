"""Native structural-entropy community detection (no external repo needed)."""
from __future__ import annotations
import numpy as np
import networkx as nx
from ..base import method
from ..se import se_agglomerative


def _cut_linkage(Z, n, k):
    """Cut a binary linkage Z into exactly k flat clusters (label 0..k-1)."""
    from scipy.cluster.hierarchy import fcluster
    if k is None or k < 1:
        k = 2
    lab = fcluster(Z, t=k, criterion="maxclust")
    # remap to 0..k-1
    uniq = {c: i for i, c in enumerate(sorted(set(lab)))}
    return [uniq[c] for c in lab]


@method("se_agglomerative", family="community_detection", is_se=True, native=True,
        paper="Li & Pan 2016 (deDoc-style greedy 2D-SE)",
        note="native: greedy merge minimizing 2D structural entropy; cut to k")
def se_agglom(G, k=None, seed=0):
    n = G.number_of_nodes()
    Z = se_agglomerative(G)
    return _cut_linkage(Z, n, k or 2)


@method("se_louvain", family="community_detection", is_se=True, native=True,
        paper="Li & Pan 2016 (2D-SE); this lib's multilevel optimizer",
        note="native: Louvain-style multilevel 2D-SE minimization (local node moves + "
             "community aggregation + multistart); merges down to k if k given. "
             "Strong replacement for the merge-only se_agglomerative.")
def se_louvain(G, k=None, seed=0):
    from ..seopt import se_optimize
    return se_optimize(G, k=k, seed=seed)


@method("se_gnn", family="community_detection", is_se=True, native=True,
        paper="this lib (ported from the author's glass-jax prototype)",
        note="attribute-aware: tiny GCN trained to minimize a differentiable soft "
             "2D structural entropy (needs jax; features from G.graph['X'], "
             "identity features if absent). k = number of communities.")
def se_gnn_method(G, k=None, seed=0):
    from ..segnn import se_gnn
    return se_gnn(G, k=k, seed=seed)


@method("se_hier", family="community_detection", is_se=True, native=True,
        paper="Li & Pan 2016 (hierarchical/encoding-tree SE); this lib's optimizer",
        note="native: encoding-tree (hierarchical) structural-entropy optimizer "
             "(binary + Louvain init, exact-guarded collapse/relocate refinement). "
             "Flat label = top level of the tree, merged down to k if given.")
def se_hier(G, k=None, seed=0):
    from ..htree import encoding_tree, top_level_labels
    from ..seopt import _merge_down_to_k
    root, deg, adj, vol = encoding_tree(G, seed=seed)
    n = G.number_of_nodes()
    labels = top_level_labels(root, n)
    if k is not None and len(set(labels)) > k:
        labels = _merge_down_to_k(G, labels, k, seed=seed)
    return labels
