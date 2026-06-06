"""Cross-check selib's ENCODING-TREE structural entropy H^T against an independent
implementation: beat-hcse's tree_entropy (Angsheng Li group's formula, a separate
code path), on trees built by selib (se_hier), the original BBM, and the original
HCSE. Writes results/se_crosscheck_tree.json.

Env: HCSE_DIR=/root/HCSE (for PartitionTree + BBM + main + partition_cut).
"""
import json, os, sys, math
import numpy as np
import networkx as nx

HCSE_DIR = os.environ.get("HCSE_DIR", "/root/HCSE")
sys.path.insert(0, HCSE_DIR)
sys.path.insert(0, os.path.join(HCSE_DIR, "hierarchical-clustering-well-clustered-graphs-main"))
from PartitionTree import PartitionTreeNode          # noqa: E402

from selib import datasets as D                       # noqa: E402
from selib.htree import (encoding_tree, linkage_to_tree, annotate, hd_se,    # noqa: E402
                         _graph_arrays, TNode)
from selib.se import se_agglomerative                 # noqa: E402


# ---- beat-hcse's INDEPENDENT H^T implementation (verbatim, different code path) ----
def graph_volume(G):
    return float(nx.volume(G, G.nodes, weight="weight"))


def node_volume(G, node):
    return float(sum(float(d.get("weight", 1.0)) for _, _, d in G.edges(node, data=True)))


def cut_value(G, left, right):
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    right = set(right); total = 0.0
    for u in left:
        for v, data in G[u].items():
            if v in right:
                total += float(data.get("weight", 1.0))
    return total


def annotate_tree(root, G):
    def visit(node):
        if not node.children:
            node.origin_node_set = {str(v) for v in node.origin_node_set}
            node.volume = sum(node_volume(G, v) for v in node.origin_node_set)
            node.g_val = node.volume; node.cut_val = 0.0; node.height = 1
            return set(node.origin_node_set)
        origin = set(); mx = 0; cl = list(node.children)
        for c in cl:
            origin |= visit(c); mx = max(mx, c.height)
        node.origin_node_set = origin
        node.volume = sum(c.volume for c in cl)
        node.cut_val = 0.0
        for i, L in enumerate(cl):
            for R in cl[i + 1:]:
                node.cut_val += cut_value(G, L.origin_node_set, R.origin_node_set)
        node.g_val = sum(c.g_val for c in cl) - 2.0 * node.cut_val
        if abs(node.g_val) < 1e-10:
            node.g_val = 0.0
        node.height = mx + 1
        return origin
    visit(root); root.parent = None
    return root


def tree_entropy(root, volume):
    if volume <= 0:
        return 0.0
    total = 0.0
    if root.children:
        for c in root.children:
            if c.volume > 0 and c.g_val > 0:
                total -= (c.g_val / volume) * np.log2(c.volume / root.volume)
            total += tree_entropy(c, volume)
    return float(total)


# ---- conversions ----
class _IdGen:
    def __init__(self): self.i = 0
    def __call__(self):
        self.i += 1; return self.i


def tnode_to_pt(tn, idg):
    if tn.is_leaf():
        p = PartitionTreeNode(); p.id = idg(); p.children = None
        p.origin_node_set = {str(tn.vertex)}; p.node_set = {str(tn.vertex): {}}; p.height = 1
        return p
    kids = [tnode_to_pt(c, idg) for c in tn.children]
    p = PartitionTreeNode(_children=set(kids)); p.id = idg()
    for k in kids:
        k.parent = p
    p.height = max(k.height for k in kids) + 1
    p.origin_node_set = set()
    return p


def pt_to_tnode(pn):
    if not pn.children:
        verts = [int(x) for x in pn.origin_node_set]
        return TNode(vertex=verts[0]) if len(verts) == 1 else TNode(children=[TNode(vertex=v) for v in verts])
    return TNode(children=[pt_to_tnode(c) for c in pn.children])


def score_both(tnode, G):
    """H^T of a selib TNode via selib.hd_se and via beat-hcse tree_entropy.
    Both scorers see the SAME graph G (its real weights, if any), and the tree is
    pruned of empty internal nodes first (beat's tree_entropy divides by parent
    volume and would hit a domain error on a volume-0 node)."""
    from selib.htree import _prune_empty
    tnode = _prune_empty(tnode)
    _, _, _, adj, deg, vol = _graph_arrays(G)
    annotate(tnode, deg, adj, vol)
    h_selib = hd_se(tnode, vol)
    Gs = nx.relabel_nodes(G, {i: str(i) for i in G.nodes()}, copy=True)  # keeps weights
    pt = tnode_to_pt(tnode, _IdGen())
    annotate_tree(pt, Gs)
    h_beat = tree_entropy(pt, graph_volume(Gs))
    return h_selib, h_beat


def bbm_tree(G, k):
    import BBM as hcse_bbm, partition_cut
    Gs = nx.relabel_nodes(G, {i: str(i) for i in G.nodes()}, copy=True)
    nx.set_edge_attributes(Gs, 1.0, "weight")

    def new_leaf(node, nid):
        leaf = PartitionTreeNode(); leaf.id = nid; leaf.children = None
        leaf.origin_node_set = {str(node)}; leaf.node_set = {str(node): {}}; leaf.height = 1
        return leaf
    clusters = partition_cut.compute_improved_partition(Gs, k) or [list(Gs.nodes)]
    hcse_bbm.id_generator = hcse_bbm.NewIDPartitionTreeNode(len(Gs.nodes) + 1)
    roots = []
    for cl in clusters:
        nodes = [str(v) for v in cl]
        roots.append(new_leaf(nodes[0], next(hcse_bbm.id_generator)) if len(nodes) == 1
                     else hcse_bbm.HuffmanMerge(Gs.subgraph(nodes).copy()))
    pn = roots[0] if len(roots) == 1 else hcse_bbm.SubHuffmanMerge(roots)
    return pt_to_tnode(pn)


def hcse_tree(G):
    import main as hcse_main
    Gs = nx.relabel_nodes(G, {i: str(i) for i in G.nodes()}, copy=True)
    nx.set_edge_attributes(Gs, 1.0, "weight")
    best = None
    for h in (3, 4, 5):
        hcse_main.id_generator = hcse_main.NewIDPartitionTreeNode(len(Gs.nodes) + 1)
        root = hcse_main.BalanceTree(hcse_main.HCSE(Gs, target_height=h, type="SE"))
        t = pt_to_tnode(root)
        _, _, _, adj, deg, vol = _graph_arrays(G)
        annotate(t, deg, adj, vol)
        v = hd_se(t, vol)
        if best is None or v < best[1]:
            best = (t, v)
    return best[0]


def graphs():
    g = [("Karate", D.karate()[0]),
         ("SBM-Clean", D.sbm(90, 3, 0.3, 0.05)[0]),
         ("LFR-mu0.2", D.lfr(n=90, mu=0.2, seed=0, avg_deg=10, max_deg=24, min_comm=8, max_comm=24)[0])]
    # disconnected
    dG = nx.disjoint_union_all([nx.gnp_random_graph(12, 0.4, seed=i) for i in range(3)])
    g.append(("disconnected-3", dG))
    # weighted
    wG = nx.gnp_random_graph(30, 0.3, seed=5)
    for u, v in wG.edges():
        wG[u][v]["weight"] = 0.5 + (u * 7 + v) % 5
    g.append(("weighted", wG))
    # graph with an ISOLATED node (degree 0) — the case that crashed se_agglomerative
    iG = nx.gnp_random_graph(20, 0.3, seed=9); iG.add_node(20)  # node 20 isolated
    g.append(("isolated-node", iG))
    return [(n, nx.convert_node_labels_to_integers(G)) for n, G in g]


def main():
    os.makedirs("results", exist_ok=True)
    recs = []
    maxdiff = 0.0
    for name, G in graphs():
      try:
        k = max(2, G.number_of_nodes() // 12)
        row = {"graph": name, "n": G.number_of_nodes()}
        # selib se_hier tree
        root, _, _, _ = encoding_tree(G, seed=0)
        a, b = score_both(root, G)
        row["se_hier"] = {"selib": round(a, 8), "beat_hcse": round(b, 8), "diff": abs(a - b)}
        maxdiff = max(maxdiff, abs(a - b))
        # naive binary dendrogram
        t = linkage_to_tree(se_agglomerative(G), G.number_of_nodes())
        a, b = score_both(t, G)
        row["se_agglom"] = {"selib": round(a, 8), "beat_hcse": round(b, 8), "diff": abs(a - b)}
        maxdiff = max(maxdiff, abs(a - b))
        # BBM / HCSE only on connected graphs — their original code is not defined
        # for disconnected inputs (HCSE emits NaN). selib handles all cases (above).
        if nx.is_connected(G):
            try:
                a, b = score_both(bbm_tree(G, k), G)
                row["bbm"] = {"selib": round(a, 8), "beat_hcse": round(b, 8), "diff": abs(a - b)}
                maxdiff = max(maxdiff, abs(a - b))
            except Exception as e:
                row["bbm"] = {"error": str(e)[:80]}
            try:
                a, b = score_both(hcse_tree(G), G)
                row["hcse"] = {"selib": round(a, 8), "beat_hcse": round(b, 8), "diff": abs(a - b)}
                maxdiff = max(maxdiff, abs(a - b))
            except Exception as e:
                row["hcse"] = {"error": str(e)[:80]}
        else:
            row["bbm"] = row["hcse"] = {"skipped": "graph not connected"}
        recs.append(row)
        print(f"[{name}] se_hier sel={row['se_hier']['selib']:.6f} beat={row['se_hier']['beat_hcse']:.6f} "
              f"| bbm diff={row.get('bbm',{}).get('diff')} | hcse diff={row.get('hcse',{}).get('diff')}", flush=True)
      except Exception as e:
        recs.append({"graph": name, "error": repr(e)[:120]})
        print(f"[{name}] ERROR {e!r}", flush=True)
    out = {"max_abs_diff": maxdiff, "n_trees": sum(len([k for k in r if isinstance(r[k], dict) and 'diff' in r[k]]) for r in recs),
           "records": recs,
           "note": "selib.hd_se (H^T) vs beat-hcse tree_entropy (independent Li-group formula), "
                   "on se_hier / se_agglom / BBM / HCSE trees over connected, disconnected and weighted graphs."}
    with open("results/se_crosscheck_tree.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE results/se_crosscheck_tree.json — max abs diff = {maxdiff:.3e}", flush=True)


if __name__ == "__main__":
    main()
