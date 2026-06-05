"""Compare selib's SE optimizers against existing work on IDENTICAL graphs.

  - 2D (flat) SE community detection: se_louvain / se_agglomerative vs classical
    (Louvain/Leiden/Infomap/spectral) vs the published SE method CoDeSEG (its
    ORIGINAL C++ code, via selib's wrapper). Metric: 2D-SE reached + NMI + #comms.
  - Hierarchical SE: se_hier vs the binary SE dendrogram vs classical agglomerative
    hierarchies (average, Ward) and Paris (scikit-network). Metric: encoding-tree
    structural entropy H^T + Dasgupta cost (both via selib's tree evaluator → fair).

Also dumps viz.json: spring-layout coordinates + se_louvain communities for a few
graphs, and the se_hier encoding tree for Karate. Output: results JSON only.
"""
import json, os, time
import numpy as np
import networkx as nx
from selib import datasets as D, metrics as M, get
from selib.se import se_agglomerative
from selib.htree import (encoding_tree, linkage_to_tree, annotate, hd_se,
                         dasgupta_tree, _graph_arrays)

# 2D-SE minimization is inherently free-k, so compare all methods at free k
# (k=None). se_agglomerative is a dendrogram method -> it appears in the
# hierarchical comparison, not here.
TWO_D = ["louvain", "leiden", "infomap", "codeseg", "se_louvain"]
STOCH = {"louvain", "leiden", "infomap", "se_louvain"}


def datasets_list():
    ds = [("Karate", D.karate),
          ("SBM-Clean", lambda: D.sbm(150, 3, 0.30, 0.05)),
          ("SBM-Noisy", lambda: D.sbm(150, 3, 0.15, 0.08))]
    for mu in (0.1, 0.3, 0.5):
        ds.append((f"LFR-mu{mu:.1f}",
                   (lambda mu=mu: D.lfr(n=150, mu=mu, seed=0, avg_deg=12, max_deg=30,
                                        min_comm=10, max_comm=40))))
    return ds


def linkage_average_ward(G, method):
    from scipy.cluster.hierarchy import linkage
    from scipy.spatial.distance import squareform
    n = G.number_of_nodes()
    sp = dict(nx.all_pairs_shortest_path_length(G))
    diam = max((max(d.values()) for d in sp.values()), default=1)
    Dm = np.full((n, n), diam + 1.0)
    for u, dd in sp.items():
        for v, dist in dd.items():
            Dm[u, v] = dist
    np.fill_diagonal(Dm, 0.0)
    Dm = (Dm + Dm.T) / 2.0
    return linkage(squareform(Dm, checks=False), method=method)


def paris_linkage(G):
    from sknetwork.hierarchy import Paris
    import scipy.sparse as sp
    A = nx.to_scipy_sparse_array(G, nodelist=list(range(G.number_of_nodes())),
                                 weight="weight", format="csr")
    A = sp.csr_matrix(A)                       # sknetwork wants a sparse matrix
    A.indices = A.indices.astype(np.int32)     # ... with int32 index arrays
    A.indptr = A.indptr.astype(np.int32)
    return Paris().fit_predict(A)


def tree_to_dict(node):
    if node.is_leaf():
        return {"leaf": int(node.vertex)}
    return {"children": [tree_to_dict(c) for c in node.children]}


def main():
    os.makedirs("results", exist_ok=True)
    twod, hier, facts = {}, {}, {}
    viz_layouts, viz_tree = {}, {}
    viz_targets = {"Karate", "SBM-Clean", "LFR-mu0.3"}

    for name, loader in datasets_list():
        try:
            G, gt = loader()
        except Exception as e:
            print(f"[skip {name}] {e}", flush=True); continue
        G = nx.convert_node_labels_to_integers(G)
        n, k = G.number_of_nodes(), len(set(gt))
        facts[name] = {"n": n, "m": G.number_of_edges(), "k_true": k}
        _, _, _, adj, deg, vol = _graph_arrays(G)

        # ---- 2D community detection ----
        td = {}
        for mn in TWO_D:
            m = get(mn)
            seeds = (0, 1, 2) if mn in STOCH else (0,)
            nmis, aris, se2s, ks = [], [], [], []
            ok = True
            for s in seeds:
                try:
                    pred = m.fit_predict(G, k=None, seed=s)   # free-k: fair SE objective
                except Exception as e:
                    print(f"[err {mn}/{name}] {e}", flush=True); ok = False; break
                nmis.append(M.nmi(gt, pred)); aris.append(M.ari(gt, pred))
                se2s.append(M.structural_entropy_2d(G, pred)); ks.append(len(set(pred)))
            if ok:
                td[mn] = {"nmi": float(np.mean(nmis)), "ari": float(np.mean(aris)),
                          "se2d": float(np.mean(se2s)), "k": float(np.mean(ks))}
        twod[name] = td

        # ---- hierarchical ----
        hd = {}
        # se_hier
        root, _, _, _ = encoding_tree(G, seed=0)
        hd["se_hier"] = {"hd_se": hd_se(root, vol), "dasgupta": dasgupta_tree(root, G)}
        # binary SE dendrogram
        t_ag = linkage_to_tree(se_agglomerative(G), n); annotate(t_ag, deg, adj, vol)
        hd["se_agglomerative"] = {"hd_se": hd_se(t_ag, vol), "dasgupta": dasgupta_tree(t_ag, G)}
        # classical linkages
        for lk in ("average", "ward"):
            try:
                t = linkage_to_tree(linkage_average_ward(G, lk), n); annotate(t, deg, adj, vol)
                hd[lk] = {"hd_se": hd_se(t, vol), "dasgupta": dasgupta_tree(t, G)}
            except Exception as e:
                print(f"[err {lk}/{name}] {e}", flush=True)
        try:
            t = linkage_to_tree(paris_linkage(G), n); annotate(t, deg, adj, vol)
            hd["paris"] = {"hd_se": hd_se(t, vol), "dasgupta": dasgupta_tree(t, G)}
        except Exception as e:
            print(f"[err paris/{name}] {e}", flush=True)
        hier[name] = hd

        # ---- viz data ----
        if name in viz_targets:
            pos = nx.spring_layout(G, seed=1, k=1.2 / (n ** 0.5))
            labels = get("se_louvain").fit_predict(G, k=k, seed=0)
            viz_layouts[name] = {
                "pos": {int(u): [round(float(p[0]), 4), round(float(p[1]), 4)] for u, p in pos.items()},
                "labels": [int(x) for x in labels],
                "edges": [[int(u), int(v)] for u, v in G.edges()],
            }
        if name == "Karate":
            viz_tree["Karate"] = tree_to_dict(root)

        print(f"[done {name}] 2D: se_louvain nmi={td.get('se_louvain',{}).get('nmi',float('nan')):.3f} "
              f"codeseg nmi={td.get('codeseg',{}).get('nmi',float('nan')):.3f} | "
              f"hier: se_hier H^T={hd['se_hier']['hd_se']:.3f}", flush=True)

    # round
    def rnd(d, nd):
        return {kk: (round(vv, nd) if isinstance(vv, float) else vv) for kk, vv in d.items()}
    for dn in twod:
        for mn in twod[dn]:
            twod[dn][mn] = rnd(twod[dn][mn], 4)
    for dn in hier:
        for mn in hier[dn]:
            hier[dn][mn] = rnd(hier[dn][mn], 4)

    with open("results/compare_results.json", "w") as f:
        json.dump({"two_d_methods": TWO_D, "datasets": list(facts.keys()),
                   "twod": twod, "hier": hier, "facts": facts}, f, indent=2)
    with open("results/viz.json", "w") as f:
        json.dump({"layouts": viz_layouts, "tree": viz_tree}, f, indent=2)
    print(f"WROTE compare_results.json ({len(facts)} datasets) + viz.json", flush=True)


if __name__ == "__main__":
    main()
