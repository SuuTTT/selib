"""Minimal SE-guided graph structure learning for node classification (~140 lines).

Distills SE-GSL (Zou et al., WWW 2023): treat the SE-optimal community
structure as the graph's low-uncertainty skeleton, then rewire -- add edges
between mutually-similar nodes inside the same SE community, drop the
lowest-similarity edges that cross communities -- and retrain a GCN.
Reports test accuracy on the original vs the rewired graph.

Usage: python min_se_gsl.py --dataset Cora --add 2 --drop_frac 0.05
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
    ei = torch.cat([edge_index, torch.arange(n).repeat(2, 1)], dim=1)
    val = torch.ones(ei.size(1))
    deg = torch.zeros(n).index_add_(0, ei[0], val)
    dinv = deg.pow(-0.5)
    return torch.sparse_coo_tensor(ei, dinv[ei[0]] * val * dinv[ei[1]], (n, n)).coalesce().to(DEV)


class GCN(torch.nn.Module):
    def __init__(self, din, hid, ncls):
        super().__init__()
        self.l1, self.l2 = torch.nn.Linear(din, hid), torch.nn.Linear(hid, ncls)

    def forward(self, A, x):
        h = F.relu(self.l1(torch.sparse.mm(A, x)))
        h = F.dropout(h, 0.5, self.training)
        return self.l2(torch.sparse.mm(A, h))


def train_eval(edge_index, data, seed, epochs=200):
    torch.manual_seed(seed)
    A = norm_adj(edge_index, data.num_nodes)
    x, y = data.x.to(DEV), data.y.to(DEV)
    model = GCN(x.size(1), 64, int(y.max()) + 1).to(DEV)
    opt = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    best_val, best_test = 0, 0
    for ep in range(epochs):
        model.train()
        loss = F.cross_entropy(model(A, x)[data.train_mask], y[data.train_mask])
        opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            pred = model(A, x).argmax(1)
        val = (pred[data.val_mask] == y[data.val_mask]).float().mean().item()
        test = (pred[data.test_mask] == y[data.test_mask]).float().mean().item()
        if val > best_val:
            best_val, best_test = val, test
    return best_test


def se_rewire(data, add_per_node=2, drop_frac=0.05, seed=0):
    n = data.num_nodes
    ei = data.edge_index.numpy()
    G = nx.Graph(); G.add_nodes_from(range(n)); G.add_edges_from(ei.T.tolist())
    labels = np.array(se_optimize(G, seed=seed))
    xn = torch.nn.functional.normalize(data.x, dim=1)
    sim = lambda u, v: float(xn[u] @ xn[v])

    # drop the lowest-similarity fraction of inter-community edges
    edges = list(G.edges())
    cross = sorted((e for e in edges if labels[e[0]] != labels[e[1]]),
                   key=lambda e: sim(*e))
    dropped = set(map(frozenset, cross[: int(len(cross) * drop_frac)]))
    kept = [e for e in edges if frozenset(e) not in dropped]

    # add top-similar intra-community non-edges (kNN restricted to the community)
    added = []
    for c in np.unique(labels):
        members = np.where(labels == c)[0]
        if len(members) < 3:
            continue
        Xc = xn[members]
        S = Xc @ Xc.T
        for row, u in enumerate(members):
            top = members[S[row].topk(min(add_per_node + 1, len(members))).indices.numpy()]
            for v in top:
                if v != u and not G.has_edge(u, v):
                    added.append((int(u), int(v)))
    new = kept + added
    new = new + [(v, u) for u, v in new]
    print(f"rewire: -{len(dropped)} cross edges, +{len(added)} intra edges "
          f"({len(np.unique(labels))} SE communities)")
    return torch.tensor(new).t()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="Cora")
    ap.add_argument("--add", type=int, default=2)
    ap.add_argument("--drop_frac", type=float, default=0.05)
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()

    data = Planetoid(root="/tmp/planetoid", name=args.dataset)[0]
    rewired = se_rewire(data, args.add, args.drop_frac)
    orig = [train_eval(data.edge_index, data, s) for s in range(args.seeds)]
    new = [train_eval(rewired, data, s) for s in range(args.seeds)]
    print(f"{args.dataset} GCN test acc, {args.seeds} seeds:")
    print(f"  original graph : {np.mean(orig):.4f} +/- {np.std(orig):.4f}")
    print(f"  SE-rewired     : {np.mean(new):.4f} +/- {np.std(new):.4f}")


if __name__ == "__main__":
    main()
