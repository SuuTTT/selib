"""Shared clustering backends for the learn/ ablations.

Every learn/ method that consumes a flat partition can swap its structure-finder:
    se             selib's validated multilevel 2D-SE minimizer
    louvain        modularity (networkx built-in)
    leiden         modularity/CPM via leidenalg (if installed)
    infomap        map equation (infomap package, if installed)
    random_matched SIZE-MATCHED random control: the SE partition's label
                   multiset, randomly permuted over nodes
This is the survey's backend ablation: does the SE-chosen membership beat
classical objectives and a granularity-matched random control inside the
SAME host method?
"""
import numpy as np


def get_clusters(G, method="se", seed=0):
    """Return integer labels aligned to list(G.nodes()).
    method "se_k<N>" = SE minimization merged down to at most N communities."""
    nodes = list(G.nodes())
    if method == "se":
        from selib.seopt import se_optimize
        return list(se_optimize(G, seed=seed))
    if method.startswith("se_k"):
        from selib.seopt import se_optimize
        return list(se_optimize(G, k=int(method[4:]), seed=seed))
    if method == "random_matched":
        from selib.seopt import se_optimize
        lab = np.array(se_optimize(G, seed=seed))
        rng = np.random.default_rng(seed)
        return list(lab[rng.permutation(len(lab))])
    if method == "louvain":
        import networkx as nx
        comms = nx.community.louvain_communities(G, seed=seed)
    elif method == "leiden":
        import igraph as ig
        import leidenalg
        g = ig.Graph(n=len(nodes),
                     edges=[(nodes.index(u), nodes.index(v)) for u, v in G.edges()]
                     if nodes != list(range(len(nodes))) else list(G.edges()))
        part = leidenalg.find_partition(g, leidenalg.ModularityVertexPartition, seed=seed)
        lab = np.zeros(len(nodes), int)
        for c, mem in enumerate(part):
            lab[list(mem)] = c
        return list(lab)
    elif method == "infomap":
        from infomap import Infomap
        im = Infomap(silent=True, seed=seed + 1)  # infomap rejects seed 0
        idx = {u: i for i, u in enumerate(nodes)}
        for u, v in G.edges():
            im.add_link(idx[u], idx[v])
        im.run()
        lab = np.zeros(len(nodes), int)
        for node in im.tree:
            if node.is_leaf:
                lab[node.node_id] = node.module_id - 1
        return list(lab)
    else:
        raise ValueError(f"unknown backend {method}")
    idx = {u: i for i, u in enumerate(nodes)}
    lab = np.zeros(len(nodes), int)
    for c, com in enumerate(comms):
        for u in com:
            lab[idx[u]] = c
    return list(lab)
