"""Quick head comparison for se_gnn: softmax vs sinkhorn on Cora/Citeseer.
Writes results/segnn_head_eval.json."""
import json, os
import numpy as np
from selib import datasets as D, metrics as M
from selib.segnn import se_gnn


def acc_hungarian(true_labels, pred_labels):
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
    out = {}
    for name in ("Cora", "Citeseer"):
        G, gt = D.REGISTRY[name]()
        k = len(set(gt))
        out[name] = {}
        for head in ("softmax", "sinkhorn"):
            nmis, aris, accs, ks = [], [], [], []
            for s in (0, 1, 2):
                pred = se_gnn(G, k=k, seed=s, head=head)
                nmis.append(M.nmi(gt, pred)); aris.append(M.ari(gt, pred))
                accs.append(acc_hungarian(gt, pred)); ks.append(len(set(pred)))
            out[name][head] = {"nmi": round(float(np.mean(nmis)), 4),
                               "ari": round(float(np.mean(aris)), 4),
                               "acc": round(float(np.mean(accs)), 4),
                               "k": round(float(np.mean(ks)), 1)}
            print(f"[{name}] {head}: {out[name][head]}", flush=True)
    with open("results/segnn_head_eval.json", "w") as f:
        json.dump(out, f, indent=2)
    print("WROTE results/segnn_head_eval.json", flush=True)


if __name__ == "__main__":
    main()
