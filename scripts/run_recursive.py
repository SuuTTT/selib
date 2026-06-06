"""Recursive triangle-fractal community structures: triangle of triangles,
triangle^3, triangle^4. Each level-k graph is 3 copies of level-(k-1) joined
pairwise — a clean nested hierarchy. We compute the SE-optimal flat partition AND
the se_hier encoding tree, to show that hierarchical structural entropy recovers
the construction's nesting (tree height tracks the recursion depth).

Output: results/recursive.json (Sierpinski layout + top-level colours + the
encoding tree serialized as a nested dict, + SE stats).
"""
import json, os, math
import networkx as nx
from selib import calc
from selib.htree import encoding_tree, hd_se, top_level_labels


def triangle_fractal(level):
    """Return (G, pos, ports). G = level-k triangle fractal; pos = Sierpinski
    geometric layout; ports = the 3 corner nodes used to connect upward."""
    if level == 1:
        G = nx.complete_graph(3)
        pos = {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (0.5, math.sqrt(3) / 2)}
        return G, pos, [0, 1, 2]
    sub, subpos, _ = triangle_fractal(level - 1)
    s = sub.number_of_nodes()
    corners = [(0.0, 0.0), (1.0, 0.0), (0.5, math.sqrt(3) / 2)]
    span = 0.46
    G = nx.Graph(); pos = {}; ports = []
    for c in range(3):
        ox, oy = corners[c]
        for v in sub.nodes():
            sx, sy = subpos[v]
            pos[v + c * s] = (ox + span * sx, oy + span * sy)
        for u, v in sub.edges():
            G.add_edge(u + c * s, v + c * s)
        ports.append(c * s)                      # node 0 of each copy = its corner
    for i in range(3):
        for j in range(i + 1, 3):
            G.add_edge(ports[i], ports[j])        # join the three copies pairwise
    return G, pos, ports


def tree_to_dict(node):
    if node.is_leaf():
        return {"leaf": int(node.vertex)}
    return {"children": [tree_to_dict(c) for c in node.children]}


def tree_height(node):
    return 1 if node.is_leaf() else 1 + max(tree_height(c) for c in node.children)


def main():
    os.makedirs("results", exist_ok=True)
    out = {"graphs": []}
    for level, label in [(2, "Triangle of triangles (3²)"),
                         (3, "Triangle³ (3³)"),
                         (4, "Triangle⁴ (3⁴)")]:
        G, pos, _ = triangle_fractal(level)
        G = nx.convert_node_labels_to_integers(G, ordering="sorted")
        n = G.number_of_nodes()
        rep = calc.se_report(G)
        root, _, _, vol = encoding_tree(G, seed=0)
        top = top_level_labels(root, n)
        out["graphs"].append({
            "name": label, "level": level,
            "n": n, "m": G.number_of_edges(),
            "se_1d": rep["se_1d"], "se_2d_opt": rep["se_2d_optimal"],
            "se_tree_opt": round(hd_se(root, vol), 6),
            "k_flat": rep["num_communities"],
            "tree_height": tree_height(root),
            "pos": {int(i): [round(float(pos[i][0]), 4), round(float(pos[i][1]), 4)] for i in range(n)},
            "labels": [int(x) for x in top],          # colour by the tree's top split
            "edges": [[int(u), int(v)] for u, v in G.edges()],
            "tree": tree_to_dict(root),
        })
        print(f"[done {label}] n={n} flat-k={rep['num_communities']} "
              f"tree_height={tree_height(root)} 1D={rep['se_1d']} "
              f"2Dopt={rep['se_2d_optimal']} HT={out['graphs'][-1]['se_tree_opt']}", flush=True)
    with open("results/recursive.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE results/recursive.json ({len(out['graphs'])} graphs)", flush=True)


if __name__ == "__main__":
    main()
