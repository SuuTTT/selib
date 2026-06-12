"""Head-to-head: SE minimization vs classical community detection (~110 lines).

The survey's superiority question in one file: on LFR benchmarks (planted
communities, mixing sweep) and Karate, compare selib's 2D-SE minimizer
against Louvain / Leiden / Infomap / size-matched random on (a) label
recovery (ARI/NMI) and (b) each method's own cross-objective 2D SE.

Usage: python min_se_clustering.py --seeds 3
"""
import argparse

import numpy as np
import networkx as nx
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from backends import get_clusters
from selib.metrics import structural_entropy_2d


def lfr(mu, seed):
    return nx.LFR_benchmark_graph(
        n=500, tau1=3.0, tau2=1.5, mu=mu, average_degree=8, max_degree=40,
        min_community=20, max_community=80, seed=seed)


def truth_labels(G):
    lab, nxt = {}, 0
    out = []
    for u in G.nodes():
        c = frozenset(G.nodes[u]["community"])
        if c not in lab:
            lab[c] = nxt; nxt += 1
        out.append(lab[c])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--methods", default="se,louvain,leiden,infomap,random_matched")
    args = ap.parse_args()
    methods = args.methods.split(",")

    cases = []
    for mu in (0.1, 0.4, 0.6):
        for s in range(args.seeds):
            try:
                G = lfr(mu, seed=10 + s)
                cases.append((f"LFR-mu{mu}", G, truth_labels(G), s))
            except nx.ExceededMaxIterations:
                pass
    K = nx.karate_club_graph()
    cases.append(("Karate", K, [0 if K.nodes[u]["club"] == "Mr. Hi" else 1
                                for u in K.nodes()], 0))

    rows = {}
    for name, G, y, s in cases:
        Gs = nx.Graph(G)  # strip LFR's frozen-set attrs / self-loops
        Gs.remove_edges_from(nx.selfloop_edges(Gs))
        for m in methods:
            try:
                lab = get_clusters(Gs, m, seed=s)
            except ImportError:
                continue
            ari = adjusted_rand_score(y, lab)
            nmi = normalized_mutual_info_score(y, lab)
            h2 = structural_entropy_2d(Gs, lab)
            rows.setdefault((name.split("-")[0] + name, m), []).append((ari, nmi, h2))

    print(f"{'case':12s} {'method':16s} {'ARI':>7s} {'NMI':>7s} {'2D-SE(bits)':>12s}")
    seen_cases = []
    for (case, m), vals in rows.items():
        if case not in seen_cases:
            seen_cases.append(case)
            print("-" * 58)
        a, n, h = map(np.mean, zip(*vals))
        print(f"{case:12s} {m:16s} {a:7.3f} {n:7.3f} {h:12.4f}")


if __name__ == "__main__":
    main()
