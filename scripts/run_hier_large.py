"""Hierarchy quality at larger scale: se_hier (first-improvement refinement) vs the
binary SE dendrogram, Paris, and BBM (original code) on LFR/SBM graphs at n=500 and
n=1000. All trees scored with selib's exact H^T evaluator. Also records wall-clock.

Run on the fleet box (HCSE repo at $HCSE_DIR for BBM). Output:
results/hier_large_results.json.
"""
import json, os, sys, time
import numpy as np
import networkx as nx
from selib import datasets as D
from selib.se import se_agglomerative
from selib.htree import (encoding_tree, linkage_to_tree, annotate, hd_se,
                         dasgupta_tree, _graph_arrays)

HCSE_DIR = os.environ.get("HCSE_DIR", "/root/HCSE")
sys.path.insert(0, HCSE_DIR)
sys.path.insert(0, os.path.join(HCSE_DIR, "hierarchical-clustering-well-clustered-graphs-main"))


def bbm_tree(G0, k):
    import BBM as hcse_bbm, partition_cut
    from PartitionTree import PartitionTreeNode
    from selib.htree import TNode
    Gs = nx.relabel_nodes(G0, {i: str(i) for i in G0.nodes()}, copy=True)
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

    def convert(p):
        if not p.children:
            verts = [int(x) for x in p.origin_node_set]
            return TNode(vertex=verts[0]) if len(verts) == 1 else \
                TNode(children=[TNode(vertex=v) for v in verts])
        return TNode(children=[convert(c) for c in p.children])
    return convert(pn)


def paris_tree(G0, n):
    from sknetwork.hierarchy import Paris
    import scipy.sparse as sp
    A = nx.to_scipy_sparse_array(G0, nodelist=list(range(n)), weight="weight", format="csr")
    A = sp.csr_matrix(A)
    A.indices = A.indices.astype(np.int32); A.indptr = A.indptr.astype(np.int32)
    return linkage_to_tree(Paris().fit_predict(A), n)


def main():
    os.makedirs("results", exist_ok=True)
    cases = [("LFR-mu0.3-n500", lambda: D.lfr(n=500, mu=0.3, seed=0)),
             ("SBM-n1000", lambda: D.sbm_scalable(n=1000, k=10, seed=0)),
             ("LFR-mu0.3-n1000", lambda: D.lfr(n=1000, mu=0.3, seed=0))]
    out = {}
    for name, loader in cases:
        try:
            G0, gt = loader()
        except Exception as e:
            print(f"[skip {name}] {e}", flush=True); continue
        G0 = nx.convert_node_labels_to_integers(G0)
        k = len(set(gt))
        _, _, n, adj, deg, vol = _graph_arrays(G0)
        rec = {}

        t0 = time.perf_counter()
        t = linkage_to_tree(se_agglomerative(G0), n); annotate(t, deg, adj, vol)
        rec["se_agglomerative"] = {"hd_se": round(hd_se(t, vol), 4),
                                   "time_s": round(time.perf_counter() - t0, 1)}
        try:
            t0 = time.perf_counter()
            t = paris_tree(G0, n); annotate(t, deg, adj, vol)
            rec["paris"] = {"hd_se": round(hd_se(t, vol), 4),
                            "time_s": round(time.perf_counter() - t0, 1)}
        except Exception as e:
            print(f"[paris err {name}] {e}", flush=True)
        try:
            t0 = time.perf_counter()
            t = bbm_tree(G0, k); annotate(t, deg, adj, vol)
            rec["bbm"] = {"hd_se": round(hd_se(t, vol), 4),
                          "time_s": round(time.perf_counter() - t0, 1)}
        except Exception as e:
            print(f"[bbm err {name}] {e}", flush=True)
        t0 = time.perf_counter()
        root, _, _, _ = encoding_tree(G0, seed=0)
        rec["se_hier"] = {"hd_se": round(hd_se(root, vol), 4),
                          "time_s": round(time.perf_counter() - t0, 1)}
        out[name] = {"n": n, "m": G0.number_of_edges(), **rec}
        print(f"[done {name}] " + " ".join(f"{m}={v['hd_se']}" for m, v in rec.items()), flush=True)

    with open("results/hier_large_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print("WROTE results/hier_large_results.json", flush=True)


if __name__ == "__main__":
    main()
