"""Worked SE tutorial examples: small graphs (some with integer-valued structural
entropy) with the full term-by-term breakdown of the 2D-SE calculation, each
cross-checked against selib.calc. Output: results/tutorial.json.

2D structural entropy:
    H2 = -sum_j (g_j/2m) log2(V_j/2m)        (module / cut term)
         -sum_v (d_v/2m) log2(d_v/V_{c(v)})  (within-community / node term)
"""
import json, os, math
import networkx as nx
from selib import calc


def breakdown(G, labels):
    """Per-community V_j, g_j and the two SE terms — the exact arithmetic."""
    deg = dict(G.degree(weight="weight"))
    two_m = sum(deg.values())
    comm = {}
    for v in G.nodes():
        comm.setdefault(labels[v], []).append(v)
    vol = {c: sum(deg[v] for v in mem) for c, mem in comm.items()}
    cut = {}
    for u, v, w in G.edges(data="weight", default=1.0):
        if labels[u] != labels[v]:
            cut[labels[u]] = cut.get(labels[u], 0.0) + w
            cut[labels[v]] = cut.get(labels[v], 0.0) + w
    rows, module, within = [], 0.0, 0.0
    for c in sorted(comm):
        Vj, gj, mem = vol[c], cut.get(c, 0.0), comm[c]
        mt = -(gj / two_m) * math.log2(Vj / two_m) if (gj > 0 and Vj > 0) else 0.0
        wt = sum(-(deg[v] / two_m) * math.log2(deg[v] / Vj)
                 for v in mem if deg[v] > 0 and Vj > 0)
        module += mt; within += wt
        rows.append({"comm": int(c), "members": [int(x) for x in mem],
                     "V": float(Vj), "g": float(gj),
                     "module_term": round(mt, 6), "within_term": round(wt, 6)})
    return {"two_m": float(two_m), "rows": rows,
            "module_total": round(module, 6), "within_total": round(within, 6),
            "H2": round(module + within, 6)}


def examples():
    ex = []

    # 1) single edge K2 — the base case, H1 = H2 = 1 bit exactly
    G = nx.path_graph(2)
    ex.append(("Single edge", G, [0, 0],
               "Two nodes, one edge. Whatever the partition, both H¹ and H² equal "
               "exactly <b>1 bit</b>: one bit to locate a random walker on one of two "
               "symmetric endpoints."))

    # 2) perfect matching: 4 disjoint edges — H1 = 3, optimal H2 = 1 (both integer)
    G = nx.Graph(); G.add_edges_from([(0, 1), (2, 3), (4, 5), (6, 7)])
    ex.append(("Four disjoint edges", G, [0, 0, 1, 1, 2, 2, 3, 3],
               "Eight nodes in four independent pairs. The partition-free 1D entropy is "
               "log₂8 = <b>3 bits</b>; describing each pair as its own community drives "
               "it down to exactly <b>1 bit</b> — the cut term vanishes (no edges leave a "
               "pair, g=0) and only the within-pair bit remains."))

    # 3) C4 (4-cycle): H1 = 2, two-block partition H2 = 1.5
    G = nx.cycle_graph(4)
    ex.append(("4-cycle, split in two", G, [0, 0, 1, 1],
               "A 4-cycle has 1D entropy log₂4 = 2 bits. Cutting it into two adjacent "
               "pairs costs a half-bit of cut entropy but saves a full bit inside the "
               "communities → H² = <b>1.5 bits</b>."))

    # 4) two triangles + bridge — the classic connected example
    G = nx.Graph(); G.add_edges_from([(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 3)])
    ex.append(("Two triangles + bridge", G, [0, 0, 0, 1, 1, 1],
               "Two triangles joined by a single bridge edge. The SE-optimal partition is "
               "the two triangles; the lone bridge is the only cut, so the module term is "
               "tiny and H² ≈ <b>1.70 bits</b> — the textbook case where SE recovers the "
               "obvious two communities."))
    return ex


def layout(G, labels):
    import sys, os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from run_gallery import community_layout
    return community_layout(G, labels, scale=0.34)


def main():
    os.makedirs("results", exist_ok=True)
    out = {"examples": []}
    for name, G, labels, note in examples():
        G = nx.convert_node_labels_to_integers(G)
        bd = breakdown(G, labels)
        h1 = calc.one_dimensional(G)
        h2_lib = calc.two_dimensional(G, labels)
        assert abs(bd["H2"] - h2_lib) < 1e-6, (name, bd["H2"], h2_lib)  # arithmetic == selib
        out["examples"].append({
            "name": name, "note": note,
            "n": G.number_of_nodes(), "m": G.number_of_edges(),
            "labels": [int(x) for x in labels],
            "se_1d": round(h1, 6), "se_2d": bd["H2"], "se_2d_selib": round(h2_lib, 6),
            "breakdown": bd,
            "pos": {int(k): v for k, v in layout(G, labels).items()},
            "edges": [[int(u), int(v)] for u, v in G.edges()],
        })
        print(f"[ok {name}] H1={h1:.4f} H2={bd['H2']:.4f} (selib {h2_lib:.4f})", flush=True)
    with open("results/tutorial.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE results/tutorial.json ({len(out['examples'])} examples)", flush=True)


if __name__ == "__main__":
    main()
