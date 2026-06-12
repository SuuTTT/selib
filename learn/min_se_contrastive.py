"""Minimal SE-guided graph contrastive learning (~150 lines).

Distills the idea behind SEGA (Wu et al., ICML 2023): the structural-entropy
hierarchy tells you which edges carry the graph's essential structure, so a
contrastive view should corrupt NON-essential edges first. GRACE-style
two-view node contrastive learning where view augmentation drops
inter-community edges (high SE cost) with low probability and
intra-community edges with high probability -- versus uniform dropping.
Evaluation: logistic-regression probe on the frozen embeddings.

Usage: python min_se_contrastive.py --dataset Cora --epochs 100
"""
import argparse

import numpy as np
import networkx as nx
import torch
import torch.nn.functional as F
from torch_geometric.datasets import Planetoid

from selib.seopt import se_optimize

DEV = "cuda" if torch.cuda.is_available() else "cpu"


def norm_adj(edge_index, n):
    ei = torch.cat([edge_index, torch.arange(n, device=edge_index.device).repeat(2, 1)], dim=1)
    val = torch.ones(ei.size(1), device=ei.device)
    deg = torch.zeros(n, device=ei.device).index_add_(0, ei[0], val)
    dinv = deg.pow(-0.5)
    return torch.sparse_coo_tensor(ei, dinv[ei[0]] * val * dinv[ei[1]], (n, n)).coalesce()


class Encoder(torch.nn.Module):
    def __init__(self, din, hid):
        super().__init__()
        self.l1, self.l2 = torch.nn.Linear(din, hid), torch.nn.Linear(hid, hid)
        self.proj = torch.nn.Sequential(torch.nn.Linear(hid, hid), torch.nn.ELU(),
                                        torch.nn.Linear(hid, hid))

    def forward(self, A, x):
        h = F.relu(self.l1(torch.sparse.mm(A, x)))
        return self.l2(torch.sparse.mm(A, h))


def nt_xent(z1, z2, tau=0.5):
    z1, z2 = F.normalize(z1, dim=1), F.normalize(z2, dim=1)
    sim = z1 @ z2.t() / tau
    return F.cross_entropy(sim, torch.arange(z1.size(0), device=z1.device))


def make_view(edge_index, drop_prob, x, feat_drop=0.2):
    keep = torch.rand(edge_index.size(1), device=edge_index.device) > drop_prob
    ei = edge_index[:, keep]
    xm = x.clone()
    xm[:, torch.rand(x.size(1), device=x.device) < feat_drop] = 0
    return ei, xm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="Cora")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--hidden", type=int, default=128)
    ap.add_argument("--p_intra", type=float, default=0.6, help="drop prob inside SE communities")
    ap.add_argument("--p_inter", type=float, default=0.1, help="drop prob across SE communities")
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()

    data = Planetoid(root="/tmp/planetoid", name=args.dataset)[0]
    n, ei = data.num_nodes, data.edge_index
    G = nx.Graph(); G.add_nodes_from(range(n)); G.add_edges_from(ei.t().tolist())
    labels = np.array(se_optimize(G, seed=0))
    print(f"{args.dataset}: {len(np.unique(labels))} SE communities")
    same = torch.tensor(labels[ei[0].numpy()] == labels[ei[1].numpy()])
    # SE-guided per-edge drop probability; uniform control matches the MEAN rate
    p_se = torch.where(same, torch.full_like(same, args.p_intra, dtype=torch.float),
                       torch.full_like(same, args.p_inter, dtype=torch.float))
    p_uni = torch.full((ei.size(1),), float(p_se.mean()))

    x = data.x.to(DEV); ei = ei.to(DEV)
    results = {}
    for name, p in (("uniform", p_uni), ("se-guided", p_se)):
        p = p.to(DEV)
        accs = []
        for seed in range(args.seeds):
            torch.manual_seed(seed)
            enc = Encoder(x.size(1), args.hidden).to(DEV)
            opt = torch.optim.Adam(enc.parameters(), lr=5e-4, weight_decay=1e-5)
            for ep in range(args.epochs):
                enc.train()
                e1, x1 = make_view(ei, p, x); e2, x2 = make_view(ei, p, x)
                z1 = enc.proj(enc(norm_adj(e1, n), x1))
                z2 = enc.proj(enc(norm_adj(e2, n), x2))
                loss = (nt_xent(z1, z2) + nt_xent(z2, z1)) / 2
                opt.zero_grad(); loss.backward(); opt.step()
            enc.eval()
            with torch.no_grad():
                z = enc(norm_adj(ei, n), x).cpu().numpy()
            from sklearn.linear_model import LogisticRegression
            clf = LogisticRegression(max_iter=3000).fit(z[data.train_mask], data.y[data.train_mask])
            accs.append(clf.score(z[data.test_mask], data.y[data.test_mask]))
        results[name] = (np.mean(accs), np.std(accs))
        print(f"{name:10s} probe acc: {np.mean(accs):.4f} +/- {np.std(accs):.4f}")
    d = results["se-guided"][0] - results["uniform"][0]
    print(f"\nSE-guided vs uniform views: {'+' if d >= 0 else ''}{d:.4f}")


if __name__ == "__main__":
    main()
