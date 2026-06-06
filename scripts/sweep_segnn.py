"""Small config sweep for se_gnn on Cora/Citeseer to try closing the DeSE gap.
Varies layers, hidden, dropout, lr; sinkhorn head fixed. Writes
results/segnn_sweep.json with NMI/ARI/ACC (3 seeds) per config."""
import json, os
import numpy as np
from selib import datasets as D, metrics as M
from selib.segnn import se_gnn
from scipy.optimize import linear_sum_assignment


def acc(t, p):
    t = np.asarray(t); p = np.asarray(p)
    tk, pk = np.unique(t), np.unique(p)
    C = np.zeros((len(pk), len(tk)))
    for i, pc in enumerate(pk):
        for j, tc in enumerate(tk):
            C[i, j] = np.sum((p == pc) & (t == tc))
    ri, ci = linear_sum_assignment(-C)
    return float(C[ri, ci].sum() / len(t))


CONFIGS = [
    {"layers": 2, "hidden": 64, "dropout": 0.0, "lr": 0.01, "iters": 300},   # current default
    {"layers": 2, "hidden": 128, "dropout": 0.5, "lr": 0.01, "iters": 400},
    {"layers": 3, "hidden": 128, "dropout": 0.5, "lr": 0.005, "iters": 500},
    {"layers": 2, "hidden": 256, "dropout": 0.6, "lr": 0.01, "iters": 400},
]


def main():
    os.makedirs("results", exist_ok=True)
    out = {}
    for name in ("Cora", "Citeseer"):
        G, gt = D.REGISTRY[name]()
        k = len(set(gt))
        out[name] = []
        for cfg in CONFIGS:
            nmis, aris, accs = [], [], []
            for s in (0, 1, 2):
                pred = se_gnn(G, k=k, seed=s, head="sinkhorn", **cfg)
                nmis.append(M.nmi(gt, pred)); aris.append(M.ari(gt, pred)); accs.append(acc(gt, pred))
            r = {**cfg, "nmi": round(np.mean(nmis), 4), "ari": round(np.mean(aris), 4),
                 "acc": round(np.mean(accs), 4)}
            out[name].append(r)
            print(f"[{name}] L{cfg['layers']} h{cfg['hidden']} d{cfg['dropout']}: "
                  f"nmi={r['nmi']} ari={r['ari']} acc={r['acc']}", flush=True)
    json.dump(out, open("results/segnn_sweep.json", "w"), indent=2)
    print("WROTE results/segnn_sweep.json", flush=True)


if __name__ == "__main__":
    main()
