"""Minimal SE coding-tree pooling for graph classification (~150 lines).

Distills SEP (Wu et al., ICML 2022): pool each graph through its structural-
entropy-optimal partition instead of a learned assignment. One SE pooling
stage (depth-2 coding tree = the SE-optimal flat clustering at free k,
computed once per graph with selib), GCN layers around it, sum readout.

Usage:  python min_sep_pooling.py --dataset MUTAG --epochs 200
Prints 10-fold cross-validated test accuracy.
"""
import argparse

import numpy as np
import networkx as nx
import torch
import torch.nn.functional as F
from torch_geometric.datasets import TUDataset

from selib.seopt import se_optimize

DEV = "cuda" if torch.cuda.is_available() else "cpu"


def norm_adj(edge_index, n):
    """Symmetrically normalized adjacency with self-loops, as a sparse tensor."""
    ei = torch.cat([edge_index, torch.arange(n).repeat(2, 1)], dim=1)
    val = torch.ones(ei.size(1))
    deg = torch.zeros(n).index_add_(0, ei[0], val)
    dinv = deg.pow(-0.5)
    val = dinv[ei[0]] * val * dinv[ei[1]]
    return torch.sparse_coo_tensor(ei, val, (n, n)).coalesce().to(DEV)


def se_assignment(edge_index, n, seed=0):
    """SE-optimal flat partition -> pooling matrix S (clusters x nodes)."""
    G = nx.Graph()
    G.add_nodes_from(range(n))
    G.add_edges_from(edge_index.t().tolist())
    labels = se_optimize(G, seed=seed) if G.number_of_edges() else [0] * n
    k = max(labels) + 1
    S = torch.zeros(k, n)
    S[torch.tensor(labels), torch.arange(n)] = 1.0
    return (S / S.sum(1, keepdim=True).clamp(min=1)).to(DEV)  # mean-pool per cluster


class GCN(torch.nn.Module):
    def __init__(self, din, dout):
        super().__init__()
        self.lin = torch.nn.Linear(din, dout)

    def forward(self, A, x):
        return F.relu(self.lin(torch.sparse.mm(A, x)))


class MinSEP(torch.nn.Module):
    def __init__(self, din, hid, ncls):
        super().__init__()
        self.g1, self.g2 = GCN(din, hid), GCN(hid, hid)
        self.head = torch.nn.Sequential(
            torch.nn.Linear(2 * hid, hid), torch.nn.ReLU(), torch.nn.Linear(hid, ncls))

    def forward(self, A, S, x):
        h1 = self.g1(A, x)
        hp = torch.mm(S, h1)                    # SE pooling: nodes -> clusters
        Ap = torch.mm(torch.mm(S, A.to_dense()), S.t())
        Ap = (Ap / Ap.sum(1, keepdim=True).clamp(min=1e-9)).to_sparse()
        h2 = self.g2(Ap, hp)
        z = torch.cat([h1.sum(0), h2.sum(0)])   # jumping-knowledge sum readout
        return self.head(z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="MUTAG")
    ap.add_argument("--epochs", type=int, default=200)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    ds = TUDataset(root="/tmp/tu", name=args.dataset)
    graphs = []
    for g in ds:
        n = g.num_nodes
        x = g.x if g.x is not None else torch.ones(n, 1)
        graphs.append((norm_adj(g.edge_index, n), se_assignment(g.edge_index, n),
                       x.float().to(DEV), int(g.y)))
    print(f"{args.dataset}: {len(graphs)} graphs prepared (SE partitions cached)")

    idx = np.random.RandomState(args.seed).permutation(len(graphs))
    folds = np.array_split(idx, 10)
    accs = []
    for f, test_idx in enumerate(folds):
        train_idx = np.setdiff1d(idx, test_idx)
        model = MinSEP(graphs[0][2].size(1), args.hidden, ds.num_classes).to(DEV)
        opt = torch.optim.Adam(model.parameters(), lr=5e-4, weight_decay=1e-4)
        for ep in range(args.epochs):
            model.train()
            np.random.shuffle(train_idx)
            for i in train_idx:
                A, S, x, y = graphs[i]
                loss = F.cross_entropy(model(A, S, x).unsqueeze(0),
                                       torch.tensor([y], device=DEV))
                opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            pred = [int(model(A, S, x).argmax()) for A, S, x, _ in (graphs[i] for i in test_idx)]
        acc = float(np.mean([p == graphs[i][3] for p, i in zip(pred, test_idx)]))
        accs.append(acc)
        print(f"fold {f}: acc {acc:.4f}")
    print(f"\nmin-SEP {args.dataset}: {np.mean(accs):.4f} +/- {np.std(accs):.4f} (10-fold)")


if __name__ == "__main__":
    main()
