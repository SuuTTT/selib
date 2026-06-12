"""Hierarchy quality: SE-agglomerative vs classical linkage (~90 lines).

The survey's positive hierarchy result in one file: build dendrograms with
selib's greedy 2D-SE agglomeration and with scipy's average/complete/Ward
linkage (on shortest-path distances), then score every tree with Dasgupta
cost (lower = better hierarchy). SE optimizes neither metric directly.

Usage: python min_se_hierarchy.py --seeds 3
"""
import argparse

import numpy as np
import networkx as nx
from scipy.cluster.hierarchy import linkage

from selib.se import se_agglomerative, dasgupta_cost


def sbm(seed, blocks=4, n=60, pin=0.3, pout=0.02):
    sizes = [n] * blocks
    p = [[pin if i == j else pout for j in range(blocks)] for i in range(blocks)]
    return nx.stochastic_block_model(sizes, p, seed=seed)


def lfr(mu, seed):
    return nx.LFR_benchmark_graph(n=300, tau1=3.0, tau2=1.5, mu=mu,
                                  average_degree=8, max_degree=40,
                                  min_community=20, max_community=60, seed=seed)


def scipy_Z(G, method):
    nodes = list(G.nodes())
    n = len(nodes)
    D = np.full((n, n), n, float)
    sp = dict(nx.all_pairs_shortest_path_length(G))
    idx = {u: i for i, u in enumerate(nodes)}
    for u, du in sp.items():
        for v, d in du.items():
            D[idx[u], idx[v]] = d
    cond = D[np.triu_indices(n, 1)]
    return linkage(cond, method=method)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()

    cases = [("SBM-4blk", sbm(s), s) for s in range(args.seeds)]
    for mu in (0.1, 0.4):
        for s in range(args.seeds):
            try:
                G = nx.Graph(lfr(mu, seed=20 + s))
                G.remove_edges_from(nx.selfloop_edges(G))
                cases.append((f"LFR-mu{mu}", G, s))
            except nx.ExceededMaxIterations:
                pass

    methods = ["se-agglom", "average", "complete", "ward"]
    table = {}
    for name, G, s in cases:
        G = nx.relabel_nodes(G, {u: i for i, u in enumerate(G.nodes())})
        for m in methods:
            Z = se_agglomerative(G) if m == "se-agglom" else scipy_Z(G, m)
            table.setdefault((name, m), []).append(dasgupta_cost(G, Z))

    print(f"{'case':10s} " + " ".join(f"{m:>10s}" for m in methods) + "   (Dasgupta cost, lower=better)")
    for case in dict.fromkeys(n for n, _ in table):
        vals = [np.mean(table[(case, m)]) for m in methods]
        best = min(vals)
        cells = " ".join(f"{'*' if v == best else ' '}{v:9.0f}" for v in vals)
        print(f"{case:10s} {cells}")


if __name__ == "__main__":
    main()
