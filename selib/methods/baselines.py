"""Non-SE community-detection baselines (native; pip deps only)."""
from __future__ import annotations
import networkx as nx
from ..base import method


def _comms_to_labels(G, comms):
    labels = [0] * G.number_of_nodes()
    pos = {n: i for i, n in enumerate(G.nodes())}
    for cid, comm in enumerate(comms):
        for v in comm:
            labels[pos[v]] = cid
    return labels


@method("louvain", family="community_detection", is_se=False,
        paper="Blondel et al. 2008 / Newman 2004", note="modularity (python-networkx)")
def louvain(G, k=None, seed=0):
    comms = nx.community.louvain_communities(G, weight="weight", seed=seed)
    return _comms_to_labels(G, comms)


@method("leiden", family="community_detection", is_se=False,
        paper="Traag et al. 2019", note="modularity (leidenalg+igraph)")
def leiden(G, k=None, seed=0):
    import igraph as ig, leidenalg
    g = ig.Graph(n=G.number_of_nodes(), edges=list(G.edges()))
    part = leidenalg.find_partition(g, leidenalg.ModularityVertexPartition, seed=seed)
    labels = [0] * G.number_of_nodes()
    for cid, comm in enumerate(part):
        for v in comm:
            labels[v] = cid
    return labels


@method("infomap", family="community_detection", is_se=False,
        paper="Rosvall & Bergstrom 2008", note="map equation (infomap)")
def infomap(G, k=None, seed=0):
    from infomap import Infomap
    im = Infomap(silent=True, num_trials=10, seed=seed + 1)
    for u, v in G.edges():
        im.add_link(int(u), int(v))
    im.run()
    labels = [0] * G.number_of_nodes()
    for node in im.tree:
        if node.is_leaf:
            labels[node.node_id] = node.module_id
    return labels


@method("spectral", family="community_detection", is_se=False,
        paper="Ng et al. 2002", note="normalized-cut spectral clustering (sklearn)")
def spectral(G, k=None, seed=0):
    from sklearn.cluster import SpectralClustering
    A = nx.to_numpy_array(G)
    sc = SpectralClustering(n_clusters=k or 2, affinity="precomputed",
                            assign_labels="kmeans", random_state=seed)
    return list(sc.fit_predict(A))
