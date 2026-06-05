"""Robustness sweep for the comparison: repeat the 2D + hierarchical comparison over
THREE graph seeds per synthetic generator (LFR/SBM realizations), reporting
mean ± half-range per (dataset, method). Strengthens the paper claims beyond the
single seed-0 graphs used in compare_results.json.

Output: results/robustness_results.json. CoDeSEG via $SELIB_CODESEG_BIN if set.
"""
import json, os
import numpy as np
import networkx as nx
from selib import datasets as D, metrics as M, get
from selib.se import se_agglomerative
from selib.htree import (encoding_tree, linkage_to_tree, annotate, hd_se,
                         dasgupta_tree, _graph_arrays)

TWO_D = ["louvain", "leiden", "infomap", "codeseg", "se_louvain"]
GRAPH_SEEDS = (0, 1, 2)


def gen(name, gseed):
    if name == "SBM-Clean":
        return D.sbm(150, 3, 0.30, 0.05, seed=gseed)
    if name == "SBM-Noisy":
        return D.sbm(150, 3, 0.15, 0.08, seed=gseed)
    mu = float(name.split("mu")[1])
    return D.lfr(n=150, mu=mu, seed=gseed, avg_deg=12, max_deg=30,
                 min_comm=10, max_comm=40)


def main():
    os.makedirs("results", exist_ok=True)
    datasets = ["SBM-Clean", "SBM-Noisy", "LFR-mu0.1", "LFR-mu0.3", "LFR-mu0.5"]
    twod, hier = {}, {}
    for name in datasets:
        acc2 = {m: {"nmi": [], "se2d": []} for m in TWO_D}
        acch = {m: {"hd_se": []} for m in ("se_hier", "se_agglomerative", "paris")}
        for gs in GRAPH_SEEDS:
            try:
                G, gt = gen(name, gs)
            except Exception as e:
                print(f"[skip {name}/g{gs}] {e}", flush=True); continue
            G = nx.convert_node_labels_to_integers(G)
            _, _, n, adj, deg, vol = _graph_arrays(G)
            for mn in TWO_D:
                try:
                    pred = get(mn).fit_predict(G, k=None, seed=0)
                    acc2[mn]["nmi"].append(M.nmi(gt, pred))
                    acc2[mn]["se2d"].append(M.structural_entropy_2d(G, pred))
                except Exception as e:
                    print(f"[err {mn}/{name}/g{gs}] {e}", flush=True)
            # hierarchical
            try:
                root, _, _, _ = encoding_tree(G, seed=0)
                acch["se_hier"]["hd_se"].append(hd_se(root, vol))
            except Exception as e:
                print(f"[err se_hier/{name}/g{gs}] {e}", flush=True)
            try:
                t = linkage_to_tree(se_agglomerative(G), n); annotate(t, deg, adj, vol)
                acch["se_agglomerative"]["hd_se"].append(hd_se(t, vol))
            except Exception as e:
                print(f"[err agglom/{name}/g{gs}] {e}", flush=True)
            try:
                from sknetwork.hierarchy import Paris
                import scipy.sparse as sp
                A = nx.to_scipy_sparse_array(G, nodelist=list(range(n)), weight="weight", format="csr")
                A = sp.csr_matrix(A); A.indices = A.indices.astype(np.int32); A.indptr = A.indptr.astype(np.int32)
                t = linkage_to_tree(Paris().fit_predict(A), n); annotate(t, deg, adj, vol)
                acch["paris"]["hd_se"].append(hd_se(t, vol))
            except Exception as e:
                print(f"[err paris/{name}/g{gs}] {e}", flush=True)
            print(f"[g{gs} done {name}]", flush=True)

        def summ(vals):
            v = [x for x in vals if x == x]
            if not v:
                return None
            return {"mean": round(float(np.mean(v)), 4),
                    "hr": round(float((max(v) - min(v)) / 2), 4), "n": len(v)}
        twod[name] = {m: {k: summ(vv) for k, vv in d.items()} for m, d in acc2.items()}
        hier[name] = {m: {k: summ(vv) for k, vv in d.items()} for m, d in acch.items()}
        print(f"[DONE {name}] se_louvain se2d={twod[name]['se_louvain']['se2d']} "
              f"| se_hier H^T={hier[name]['se_hier']['hd_se']}", flush=True)

    with open("results/robustness_results.json", "w") as f:
        json.dump({"graph_seeds": list(GRAPH_SEEDS), "twod": twod, "hier": hier}, f, indent=2)
    print("WROTE results/robustness_results.json", flush=True)


if __name__ == "__main__":
    main()
