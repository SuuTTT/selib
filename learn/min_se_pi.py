"""P6 validation: query-biased (bring-your-own-pi) SE vs uniform-degree SE (~100 lines).

Thesis: with pi = personalized PageRank centered on a query node, SE-minimization
spends its resolution budget near the query -- finely resolving the query's own
community while coarsening distant regions -- so it should recover the query's
true community BETTER than uniform-degree SE, especially when the graph is large
enough that uniform SE under- or mis-resolves the local structure.

Testbed: planted SBM, query node in block 0; metric = F1 of recovering block 0
as the query node's predicted cluster, query-biased pi vs uniform pi.

Usage: python min_se_pi.py --seeds 5
"""
import argparse
import numpy as np
import networkx as nx

from selib.sepi import degree_pi, ppr_pi, ppr_transition, optimize_pi, se2d_pi, se2d_pi_selftest, _adj_P


def block_f1(labels, truth_block_mask, query_idx):
    """F1 of the query's predicted cluster against the query's true block."""
    pred = np.asarray(labels) == labels[query_idx]
    tp = (pred & truth_block_mask).sum()
    fp = (pred & ~truth_block_mask).sum()
    fn = (~pred & truth_block_mask).sum()
    if tp == 0:
        return 0.0
    prec, rec = tp / (tp + fp), tp / (tp + fn)
    return 2 * prec * rec / (prec + rec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--blocks", type=int, default=8)
    ap.add_argument("--block_size", type=int, default=40)
    ap.add_argument("--pin", type=float, default=0.25)
    ap.add_argument("--pout", type=float, default=0.02)
    ap.add_argument("--alpha", type=float, default=0.15)
    args = ap.parse_args()

    err = se2d_pi_selftest()
    print(f"[gate] se2d_pi vs standard SE (pi=degree) max abs err = {err:.2e}  "
          f"{'PASS' if err < 1e-9 else 'FAIL'}")
    if err >= 1e-9:
        return

    unif_f1, qb_f1 = [], []
    for s in range(args.seeds):
        sizes = [args.block_size] * args.blocks
        p = [[args.pin if i == j else args.pout for j in range(args.blocks)]
             for i in range(args.blocks)]
        G = nx.stochastic_block_model(sizes, p, seed=s)
        nodes = list(G.nodes())
        truth = np.array([n // args.block_size for n in range(len(nodes))])
        query = 0                                    # a node in block 0
        block0 = truth == 0

        _, _, A, P_walk, _ = _adj_P(G)
        pi_u = degree_pi(G)
        pi_q = ppr_pi(G, query, alpha=args.alpha)
        P_q = ppr_transition(G, query, alpha=args.alpha)

        lab_u = optimize_pi(G, pi_u, P_walk, seed=s)
        lab_q = optimize_pi(G, pi_q, P_q, seed=s)
        f1u = block_f1(lab_u, block0, query)
        f1q = block_f1(lab_q, block0, query)
        unif_f1.append(f1u); qb_f1.append(f1q)
        print(f"seed {s}: uniform-pi F1(query block)={f1u:.3f} | "
              f"query-biased-pi F1={f1q:.3f} | #clusters {len(set(lab_u))}/{len(set(lab_q))}")

    print(f"\nquery-block recovery F1 over {args.seeds} seeds:")
    print(f"  uniform-degree pi : {np.mean(unif_f1):.3f} +/- {np.std(unif_f1):.3f}")
    print(f"  query-biased pi   : {np.mean(qb_f1):.3f} +/- {np.std(qb_f1):.3f}")
    d = np.mean(qb_f1) - np.mean(unif_f1)
    print(f"  delta (query-biased - uniform): {'+' if d >= 0 else ''}{d:.3f}")


if __name__ == "__main__":
    main()
