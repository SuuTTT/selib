"""Dataset generators + loaders + exporters for the SE benchmark.

Returns (G: nx.Graph with integer nodes 0..N-1, labels: list[int] ground truth).
LFR is the canonical community-detection difficulty axis (vary mu); SBM gives a
controlled clean/noisy contrast; real graphs test the topology-vs-semantics gap.

Exporters convert a graph to the input format each original repo expects, so we
feed *identical* graphs to every method (fair comparison).
"""
from __future__ import annotations
import os
import networkx as nx
import numpy as np


# ---------------- generators ----------------
def lfr(n=1000, mu=0.3, seed=0, avg_deg=20, max_deg=50,
        tau1=2.5, tau2=1.5, min_comm=20, max_comm=100):
    """LFR benchmark graph. mu = mixing parameter (fraction of inter-community
    edges); higher mu = harder. Returns simple undirected graph + labels."""
    G = nx.LFR_benchmark_graph(
        n, tau1, tau2, mu, average_degree=avg_deg, max_degree=max_deg,
        min_community=min_comm, max_community=max_comm, seed=seed)
    G.remove_edges_from(nx.selfloop_edges(G))
    G = nx.convert_node_labels_to_integers(G, label_attribute="old")
    # ground truth communities are stored per-node in 'community'
    labels = [-1] * G.number_of_nodes()
    comm_id = {}
    for n_ in G.nodes():
        comm = frozenset(G.nodes[n_]["community"])
        labels[n_] = comm_id.setdefault(comm, len(comm_id))
    return nx.Graph(G), labels


def sbm(n=150, k=3, p_in=0.3, p_out=0.05, seed=0):
    sizes = [n // k] * k
    sizes[-1] += n - sum(sizes)
    P = np.full((k, k), p_out)
    np.fill_diagonal(P, p_in)
    G = nx.stochastic_block_model(sizes, P, seed=seed)
    labels = []
    for b, s in enumerate(sizes):
        labels += [b] * s
    return nx.Graph(G), labels


def sbm_scalable(n=1000, k=10, intra_deg=15, inter_deg=3, seed=0):
    """SBM whose community signal is held CONSTANT as N grows: each node keeps
    ~intra_deg within-block and ~inter_deg cross-block edges regardless of n, so
    accuracy-vs-N is not confounded by the detection threshold (unlike a fixed
    p_in/p_out SBM, where large N inverts the signal). Use for scalability runs."""
    sizes = [n // k] * k
    sizes[-1] += n - sum(sizes)
    b = n // k
    p_in = min(1.0, intra_deg / max(1, b - 1))
    p_out = min(1.0, inter_deg / max(1, n - b))
    P = np.full((k, k), p_out)
    np.fill_diagonal(P, p_in)
    G = nx.stochastic_block_model(sizes, P, seed=seed)
    labels = []
    for bk, s in enumerate(sizes):
        labels += [bk] * s
    return nx.Graph(G), labels


def karate():
    G = nx.karate_club_graph()
    labels = [0 if G.nodes[n]["club"] == "Mr. Hi" else 1 for n in G.nodes()]
    G = nx.convert_node_labels_to_integers(G)
    return G, labels


def football():
    """American college football; ground-truth conferences. Downloads gml."""
    url = "http://www-personal.umich.edu/~mejn/netdata/football.zip"
    import urllib.request, zipfile, io
    raw = urllib.request.urlopen(url, timeout=30).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    gml = z.read("football.gml").decode("latin-1")
    # strip leading comment lines gml parser dislikes
    gml = "\n".join(l for l in gml.splitlines() if not l.strip().startswith("Creator"))
    G = nx.parse_gml(gml)
    labels_attr = nx.get_node_attributes(G, "value")
    G = nx.convert_node_labels_to_integers(G, ordering="sorted", label_attribute="old")
    labels = [labels_attr[G.nodes[n]["old"]] for n in G.nodes()]
    return nx.Graph(G), labels


REGISTRY = {
    "Karate": karate,
    "SBM-Clean": lambda: sbm(150, 3, 0.30, 0.05),
    "SBM-Noisy": lambda: sbm(150, 3, 0.15, 0.08),
    "Football": football,
    # LFR sweeps are parameterized; call lfr(mu=...) directly in runners.
}


# ---------------- exporters ----------------
def to_edgelist(G, path, one_based=False, weighted=False, sep=" "):
    off = 1 if one_based else 0
    with open(path, "w") as f:
        for u, v, d in G.edges(data=True):
            if weighted:
                f.write(f"{u+off}{sep}{v+off}{sep}{d.get('weight',1.0)}\n")
            else:
                f.write(f"{u+off}{sep}{v+off}\n")


def to_communities_file(labels, path, one_based=True, sep="\t"):
    """One community per line (node ids). Inverse of node->label. For CoDeSEG."""
    from collections import defaultdict
    off = 1 if one_based else 0
    groups = defaultdict(list)
    for node, lab in enumerate(labels):
        groups[lab].append(node + off)
    with open(path, "w") as f:
        for comm in groups.values():
            f.write(sep.join(map(str, comm)) + "\n")


def communities_file_to_labels(path, n, one_based=True):
    """Parse a one-community-per-line file back to a labels list of length n."""
    off = 1 if one_based else 0
    labels = [-1] * n
    with open(path) as f:
        for cid, line in enumerate(l for l in f if l.strip()):
            for tok in line.split():
                v = int(tok) - off
                if 0 <= v < n:
                    labels[v] = cid
    nxt = max(labels) + 1
    for i in range(n):
        if labels[i] == -1:
            labels[i] = nxt; nxt += 1
    return labels


def to_dedoc(G, path):
    """deDoc format: first line = #nodes; then `u v weight` (1-based, symmetric)."""
    n = G.number_of_nodes()
    with open(path, "w") as f:
        f.write(f"{n}\n")
        for u, v, d in G.edges(data=True):
            f.write(f"{u+1} {v+1} {float(d.get('weight',1.0))}\n")


def save_labels(labels, path):
    with open(path, "w") as f:
        for x in labels:
            f.write(f"{x}\n")
