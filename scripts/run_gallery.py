"""Compute SE-optimal partitions of classical graphs for the gallery page.
For each graph: the optimal 2D-SE partition (se_louvain, free k), a layout, and
the SE statistics (1D, optimal 2D, optimal H^T, #communities). Output:
results/gallery.json — consumed by scripts/build_gallery.py.
"""
import json, os
import networkx as nx
from selib import calc, datasets as D


def _graphs():
    g = []

    def add(name, G, pos=None, note=""):
        g.append((name, G, pos, note))

    add("Karate club", nx.karate_club_graph(), note="Zachary 1977 — the canonical split")
    add("Les Misérables", nx.les_miserables_graph(), note="co-appearance of characters")
    add("Florentine families", nx.florentine_families_graph(), note="Renaissance marriage ties")
    add("Caveman (4×6)", nx.connected_caveman_graph(4, 6), note="planted near-cliques")
    add("Petersen", nx.petersen_graph(), note="vertex-transitive — no community structure")
    add("Balanced tree (b2,d4)", nx.balanced_tree(2, 4), note="pure hierarchy")
    # 2D grid keeps its geometric layout
    G = nx.grid_2d_graph(6, 6)
    pos = {i: [float(x), float(y)] for i, (x, y) in enumerate(G.nodes())}
    add("Grid 6×6", nx.convert_node_labels_to_integers(G), pos=pos, note="lattice — weak structure")
    add("SBM 3-block", D.sbm(150, 3, 0.30, 0.05)[0], note="planted blocks (clean)")
    add("LFR μ=0.2", D.lfr(n=150, mu=0.2, seed=0, avg_deg=12, max_deg=30,
                          min_comm=10, max_comm=40)[0], note="LFR benchmark, easy regime")
    return g


def main():
    os.makedirs("results", exist_ok=True)
    out = {"graphs": []}
    for name, G, pos, note in _graphs():
        G = nx.convert_node_labels_to_integers(G)
        n = G.number_of_nodes()
        labels, se2 = calc.optimal_2d(G)
        rep = calc.se_report(G)
        if pos is None:
            p = nx.spring_layout(G, seed=7, k=1.3 / (n ** 0.5))
            pos = {int(u): [round(float(v[0]), 4), round(float(v[1]), 4)] for u, v in p.items()}
        out["graphs"].append({
            "name": name, "note": note,
            "n": n, "m": G.number_of_edges(),
            "se_1d": rep["se_1d"], "se_2d_opt": rep["se_2d_optimal"],
            "se_tree_opt": rep["se_tree_optimal"], "k": rep["num_communities"],
            "compression": rep["compression_2d"],
            "pos": {int(k): v for k, v in pos.items()},
            "labels": [int(x) for x in labels],
            "edges": [[int(u), int(v)] for u, v in G.edges()],
        })
        print(f"[done {name}] n={n} k={rep['num_communities']} "
              f"1D={rep['se_1d']} 2Dopt={rep['se_2d_optimal']} HT={rep['se_tree_optimal']}", flush=True)

    with open("results/gallery.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE results/gallery.json ({len(out['graphs'])} graphs)", flush=True)


if __name__ == "__main__":
    main()
