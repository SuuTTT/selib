"""Compute SE-optimal partitions of classical graphs for the gallery page.
For each graph: the optimal 2D-SE partition (se_louvain, free k), a layout, and
the SE statistics (1D, optimal 2D, optimal H^T, #communities). Output:
results/gallery.json — consumed by scripts/build_gallery.py.
"""
import json, os
import numpy as np
import networkx as nx
from selib import calc, datasets as D


def community_layout(G, labels, seed=7, scale=0.26):
    """Two-level layout: lay out the *community graph* to place each community,
    then spring-lay-out each community locally around its centre — so nodes of the
    same label end up geometrically close."""
    comms = {}
    for v, l in enumerate(labels):
        comms.setdefault(l, []).append(v)
    CG = nx.Graph(); CG.add_nodes_from(comms)
    for u, v in G.edges():
        a, b = labels[u], labels[v]
        if a != b:
            CG.add_edge(a, b, weight=CG.get_edge_data(a, b, {}).get("weight", 0) + 1)
    if CG.number_of_nodes() == 1:
        centers = {next(iter(comms)): np.array([0.0, 0.0])}
    elif CG.number_of_edges() > 0:
        centers = nx.spring_layout(CG, seed=seed, k=2.0, weight="weight", iterations=200)
    else:
        centers = nx.circular_layout(CG)
    pos = {}
    for l, members in comms.items():
        sub = G.subgraph(members)
        if len(members) > 1:
            sp = nx.spring_layout(sub, seed=seed, k=0.9, iterations=120)
        else:
            sp = {members[0]: np.array([0.0, 0.0])}
        cx, cy = centers[l]
        for v in members:
            pos[v] = [round(float(cx + scale * sp[v][0]), 4),
                      round(float(cy + scale * sp[v][1]), 4)]
    return pos


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
    # grid keeps its true lattice geometry (community layout would hide the lattice)
    Ggrid = nx.grid_2d_graph(6, 6)
    grid_pos = {i: [float(x), float(y)] for i, (x, y) in enumerate(Ggrid.nodes())}
    add("Grid 6×6", nx.convert_node_labels_to_integers(Ggrid), pos=grid_pos,
        note="lattice — geometric layout kept; weak community structure")
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
        # geometric graphs (grid) keep their layout; everything else clusters by community
        pos = pos if pos is not None else community_layout(G, labels)
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
