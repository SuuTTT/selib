"""Attributed-graph benchmark: se_gnn (attribute-aware differentiable SE + GCN) vs
topology-only methods on Cora / Citeseer (standard Planetoid splits, features on
G.graph['X']). Metrics: NMI, ARI, ACC (Hungarian), 2D-SE reached, #communities.

Output: results/attr_results.json — every number from this run.
"""
import json, os, time
import numpy as np
from selib import datasets as D, metrics as M, get

METHODS = ["se_gnn", "se_louvain", "louvain", "leiden", "infomap", "spectral"]
STOCH = {"se_gnn", "se_louvain", "louvain", "leiden", "infomap", "spectral"}
SEEDS = (0, 1, 2)


def acc_hungarian(true_labels, pred_labels):
    """Clustering accuracy with optimal label matching (Hungarian)."""
    from scipy.optimize import linear_sum_assignment
    t = np.asarray(true_labels); p = np.asarray(pred_labels)
    tk = np.unique(t); pk = np.unique(p)
    Cm = np.zeros((len(pk), len(tk)))
    for i, pc in enumerate(pk):
        for j, tc in enumerate(tk):
            Cm[i, j] = np.sum((p == pc) & (t == tc))
    ri, ci = linear_sum_assignment(-Cm)
    return float(Cm[ri, ci].sum() / len(t))


def main():
    os.makedirs("results", exist_ok=True)
    out = {"methods": METHODS, "table": {}, "facts": {}}
    for name in ("Cora", "Citeseer"):
        try:
            G, gt = D.REGISTRY[name]()
        except Exception as e:
            print(f"[skip {name}] {e}", flush=True); continue
        k = len(set(gt))
        out["facts"][name] = {"n": G.number_of_nodes(), "m": G.number_of_edges(),
                              "k_true": k, "d_feat": int(G.graph["X"].shape[1])}
        row = {}
        for mn in METHODS:
            m = get(mn)
            seeds = SEEDS if mn in STOCH else (0,)
            nmis, aris, accs, se2s, ks, ts = [], [], [], [], [], []
            ok = True
            for s in seeds:
                t0 = time.perf_counter()
                try:
                    pred = m.fit_predict(G, k=k, seed=s)
                except Exception as e:
                    print(f"[err {mn}/{name}] {e}", flush=True); ok = False; break
                ts.append(time.perf_counter() - t0)
                nmis.append(M.nmi(gt, pred)); aris.append(M.ari(gt, pred))
                accs.append(acc_hungarian(gt, pred))
                se2s.append(M.structural_entropy_2d(G, pred)); ks.append(len(set(pred)))
            if ok:
                row[mn] = {"nmi": round(float(np.mean(nmis)), 4),
                           "ari": round(float(np.mean(aris)), 4),
                           "acc": round(float(np.mean(accs)), 4),
                           "se2d": round(float(np.mean(se2s)), 4),
                           "k": round(float(np.mean(ks)), 1),
                           "time_s": round(float(np.mean(ts)), 2)}
                print(f"[{name}] {mn}: nmi={row[mn]['nmi']} ari={row[mn]['ari']} "
                      f"acc={row[mn]['acc']} k={row[mn]['k']}", flush=True)
        out["table"][name] = row
        print(f"[done {name}]", flush=True)

    with open("results/attr_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"WROTE results/attr_results.json", flush=True)


if __name__ == "__main__":
    main()
