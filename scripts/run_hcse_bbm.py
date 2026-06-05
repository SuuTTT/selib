"""Run the ORIGINAL HCSE and BBM hierarchical SE code (github.com/Hardict/HCSE) on
selib's identical graphs, convert their PartitionTreeNode trees to selib trees, and
score with selib's own H^T + Dasgupta evaluators (so all hierarchical methods are
compared on exactly the same objective).

Runs on the fleet box where the HCSE repo is cloned at $HCSE_DIR (default /root/HCSE).
Output: results/hcse_bbm_results.json.
"""
import os, sys, json
import networkx as nx

HCSE_DIR = os.environ.get("HCSE_DIR", "/root/HCSE")
sys.path.insert(0, HCSE_DIR)
sys.path.insert(0, os.path.join(HCSE_DIR, "hierarchical-clustering-well-clustered-graphs-main"))

import main as hcse_main          # noqa: E402
import BBM as hcse_bbm            # noqa: E402
import partition_cut             # noqa: E402
from PartitionTree import PartitionTreeNode  # noqa: E402

from selib import datasets as D   # noqa: E402
from selib.htree import TNode, annotate, hd_se, dasgupta_tree, _graph_arrays  # noqa: E402


def new_leaf(node, nid):
    leaf = PartitionTreeNode()
    leaf.id = nid
    leaf.children = None
    leaf.origin_node_set = {str(node)}
    leaf.node_set = {str(node): {}}
    leaf.height = 1
    return leaf


def run_bbm(G, k):
    clusters = partition_cut.compute_improved_partition(G, k)
    if not clusters:
        clusters = [list(G.nodes)]
    hcse_bbm.id_generator = hcse_bbm.NewIDPartitionTreeNode(len(G.nodes) + 1)
    roots = []
    for cl in clusters:
        nodes = [str(v) for v in cl]
        if len(nodes) == 1:
            root = new_leaf(nodes[0], next(hcse_bbm.id_generator))
        else:
            root = hcse_bbm.HuffmanMerge(G.subgraph(nodes).copy())
        roots.append(root)
    return roots[0] if len(roots) == 1 else hcse_bbm.SubHuffmanMerge(roots)


def run_hcse(G, target_height):
    hcse_main.id_generator = hcse_main.NewIDPartitionTreeNode(len(G.nodes) + 1)
    root = hcse_main.HCSE(G, target_height=target_height, type="SE")
    return hcse_main.BalanceTree(root)


def convert(pn):
    """PartitionTreeNode -> selib TNode with leaves = individual graph vertices.

    HCSE stops at communities, so a childless node can hold MANY vertices; we expand
    such a community into singleton leaf children (canonical encoding-tree scoring,
    leaves = vertices — the same convention used for se_hier / BBM / Paris)."""
    if not pn.children:
        verts = [int(x) for x in pn.origin_node_set]
        if len(verts) == 1:
            return TNode(vertex=verts[0])
        return TNode(children=[TNode(vertex=v) for v in verts])
    return TNode(children=[convert(c) for c in pn.children])


def datasets_list():
    ds = [("Karate", D.karate),
          ("SBM-Clean", lambda: D.sbm(150, 3, 0.30, 0.05)),
          ("SBM-Noisy", lambda: D.sbm(150, 3, 0.15, 0.08))]
    for mu in (0.1, 0.3, 0.5):
        ds.append((f"LFR-mu{mu:.1f}",
                   (lambda mu=mu: D.lfr(n=150, mu=mu, seed=0, avg_deg=12, max_deg=30,
                                        min_comm=10, max_comm=40))))
    return ds


def score(tnode, G0, deg, adj, vol):
    annotate(tnode, deg, adj, vol)
    return {"hd_se": round(hd_se(tnode, vol), 4), "dasgupta": round(dasgupta_tree(tnode, G0), 1)}


def main():
    os.makedirs("results", exist_ok=True)
    out = {"methods": ["hcse", "bbm"], "records": {}}
    for name, loader in datasets_list():
        try:
            G0, gt = loader()
        except Exception as e:
            print(f"[skip {name}] {e}", flush=True); continue
        G0 = nx.convert_node_labels_to_integers(G0)
        k = len(set(gt))
        _, _, n, adj, deg, vol = _graph_arrays(G0)
        # str-labelled, weighted graph for HCSE/BBM (their code reads 'weight')
        Gs = nx.relabel_nodes(G0, {i: str(i) for i in G0.nodes()}, copy=True)
        nx.set_edge_attributes(Gs, 1.0, "weight")
        rec = {}
        # HCSE: sweep target_height, keep lowest H^T (its best hierarchy)
        best = None
        for h in (2, 3, 4, 5, 6):
            try:
                t = convert(run_hcse(Gs, h))
                s = score(t, G0, deg, adj, vol)
                if best is None or s["hd_se"] < best["hd_se"]:
                    best = s; best["height"] = h
            except Exception as e:
                print(f"[hcse h={h} err {name}] {e}", flush=True)
        if best:
            rec["hcse"] = best
        # BBM with k = ground-truth #communities
        try:
            rec["bbm"] = score(convert(run_bbm(Gs, k)), G0, deg, adj, vol)
        except Exception as e:
            print(f"[bbm err {name}] {e}", flush=True)
        out["records"][name] = rec
        print(f"[done {name}] hcse H^T={rec.get('hcse',{}).get('hd_se')} "
              f"bbm H^T={rec.get('bbm',{}).get('hd_se')}", flush=True)

    with open("results/hcse_bbm_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE results/hcse_bbm_results.json ({len(out['records'])} datasets)", flush=True)


if __name__ == "__main__":
    main()
