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
