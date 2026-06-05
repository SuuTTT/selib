"""Hierarchy-quality benchmark: encoding-tree structural entropy (H^T) and Dasgupta
cost of selib's hierarchical optimizer vs. the naive binary SE dendrogram and a flat
(2-level) Louvain hierarchy. Lower is better for both objectives.

Output: results/hier_results.json — every number from a tree this script built.
"""
import json, os, time
import networkx as nx
from selib import datasets as D
from selib.se import se_agglomerative
from selib.htree import (encoding_tree, linkage_to_tree, annotate, hd_se,
                         dasgupta_tree, TNode, _graph_arrays)


def louvain_two_level(G, seed):
    import networkx as nx
    comms = nx.community.louvain_communities(G, weight="weight", seed=seed)
    pos = {u: i for i, u in enumerate(G.nodes())}
    children = []
    for c in comms:
        children.append(TNode(children=[TNode(vertex=pos[v]) for v in c]))
    return TNode(children=children)


def datasets_block():
    ds = [("Karate", D.karate),
          ("SBM-Clean", lambda: D.sbm(150, 3, 0.30, 0.05)),
          ("SBM-Noisy", lambda: D.sbm(150, 3, 0.15, 0.08))]
    for mu in (0.1, 0.3, 0.5):
        ds.append((f"LFR-mu{mu:.1f}", (lambda mu=mu: D.lfr(n=150, mu=mu, seed=0,
                                                           avg_deg=12, max_deg=30,
                                                           min_comm=10, max_comm=40))))
    return ds


def main():
    os.makedirs("results", exist_ok=True)
    records = []
    for name, loader in datasets_block():
        try:
            G, _ = loader()
        except Exception as e:
            print(f"[skip {name}] {e}", flush=True); continue
        G = nx.convert_node_labels_to_integers(G)
        _, _, n, adj, deg, vol = _graph_arrays(G)

        # 1) naive binary SE dendrogram
        Z = se_agglomerative(G)
        t_ag = linkage_to_tree(Z, n); annotate(t_ag, deg, adj, vol)
        rec_ag = {"method": "se_agglomerative", "dataset": name,
                  "hd_se": hd_se(t_ag, vol), "dasgupta": dasgupta_tree(t_ag, G),
                  "n": n, "m": G.number_of_edges()}

        # 2) flat Louvain 2-level hierarchy
        t_lv = louvain_two_level(G, seed=0); annotate(t_lv, deg, adj, vol)
        rec_lv = {"method": "louvain_2level", "dataset": name,
                  "hd_se": hd_se(t_lv, vol), "dasgupta": dasgupta_tree(t_lv, G),
                  "n": n, "m": G.number_of_edges()}

        # 3) selib hierarchical optimizer (build + refine), best of a few seeds
        t0 = time.perf_counter()
        best = None
        for s in range(2):
            root, deg2, adj2, vol2 = encoding_tree(G, seed=s, starts=4, do_refine=True)
            h = hd_se(root, vol2)
            if best is None or h < best[0]:
                best = (h, root)
        dt = time.perf_counter() - t0
        rec_hi = {"method": "se_hier", "dataset": name,
                  "hd_se": best[0], "dasgupta": dasgupta_tree(best[1], G),
                  "time_s": round(dt, 3), "n": n, "m": G.number_of_edges()}

        for r in (rec_ag, rec_lv, rec_hi):
            r["hd_se"] = round(r["hd_se"], 6); r["dasgupta"] = round(r["dasgupta"], 1)
            records.append(r)
        print(f"[done {name}] agglom H^T={rec_ag['hd_se']:.4f} | "
              f"louvain2L={rec_lv['hd_se']:.4f} | se_hier={rec_hi['hd_se']:.4f}", flush=True)

    out = {"methods": ["se_agglomerative", "louvain_2level", "se_hier"],
           "objective": "encoding-tree structural entropy (H^T) and Dasgupta cost; lower better",
           "records": records}
    with open("results/hier_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE results/hier_results.json with {len(records)} records", flush=True)


if __name__ == "__main__":
    main()
