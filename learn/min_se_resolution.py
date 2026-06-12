"""Resolution behavior of clustering objectives: ring of cliques (~100 lines).

The classic testbed (Fortunato & Barthelemy 2007): r cliques of size c joined
in a ring by single edges. Modularity has a RESOLUTION LIMIT - when r is
large it merges adjacent cliques. Free-k SE minimization has the OPPOSITE
failure: it can over-resolve. K-constrained SE (se_optimize_fixed_k, ported
from seclust-targetk's SE-HybridK) is the fix: optimize SE inside the
K-cluster subspace. Ground truth = one community per clique.

Usage: python min_se_resolution.py
"""
import argparse

import numpy as np
import networkx as nx
from sklearn.metrics import adjusted_rand_score

from backends import get_clusters
from selib.seopt import se_optimize_fixed_k
from selib.metrics import structural_entropy_2d


def ring_of_cliques(r, c, seed=0):
    G = nx.ring_of_cliques(r, c)
    y = [i // c for i in range(r * c)]
    return G, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clique_size", type=int, default=5)
    ap.add_argument("--rings", default="8,16,24,32,48")
    args = ap.parse_args()
    c = args.clique_size

    print(f"ring of cliques, clique size {c}; truth = one community per clique")
    print(f"{'r':>4s} {'method':16s} {'#found':>7s} {'ARI':>7s} {'H2(bits)':>9s}")
    for r in map(int, args.rings.split(",")):
        G, y = ring_of_cliques(r, c)
        rows = []
        for m in ("louvain", "leiden", "se"):
            try:
                lab = get_clusters(G, m, seed=0)
            except ImportError:
                continue
            rows.append((m, lab))
        rows.append((f"se_fixed_k{r}", se_optimize_fixed_k(G, k=r, seed=0)))
        print("-" * 50)
        for name, lab in rows:
            print(f"{r:4d} {name:16s} {len(set(lab)):7d} "
                  f"{adjusted_rand_score(y, lab):7.3f} "
                  f"{structural_entropy_2d(G, lab):9.4f}")


if __name__ == "__main__":
    main()
