"""Minimal SE-cluster exploration bonus for tabular RL (~150 lines).

Distills the mechanism of SI2E (Zeng et al., NeurIPS 2024) to its tabular
essence: build the state-transition graph from experience, cluster it by
minimizing structural entropy (selib), and pay the exploration bonus at the
CLUSTER level (novel regions) on top of state-level novelty. Compared against
plain count-based novelty and no bonus, on a four-rooms gridworld with a
sparse terminal reward. No gym, no GPU - numpy only.

Usage: python min_se_exploration.py --episodes 300 --seeds 5
"""
import argparse

import numpy as np
import networkx as nx

from selib.seopt import se_optimize

N = 11  # grid side; four rooms with doorways


def build_grid():
    walls = np.zeros((N, N), bool)
    walls[N // 2, :] = True; walls[:, N // 2] = True
    for d in ((N // 2, N // 4), (N // 2, 3 * N // 4), (N // 4, N // 2), (3 * N // 4, N // 2)):
        walls[d] = False
    return walls


WALLS = build_grid()
START, GOAL = (0, 0), (N - 1, N - 1)
MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def step(s, a):
    ni, nj = s[0] + MOVES[a][0], s[1] + MOVES[a][1]
    if 0 <= ni < N and 0 <= nj < N and not WALLS[ni, nj]:
        s = (ni, nj)
    return s, (1.0 if s == GOAL else 0.0), s == GOAL


def run(bonus, episodes, seed, beta=0.05, recluster=500):
    rng = np.random.default_rng(seed)
    Q = np.zeros((N, N, 4))
    counts = np.zeros((N, N))
    G = nx.Graph()
    labels, cl_counts, t = {}, None, 0
    solved_at = None
    for ep in range(episodes):
        s, done, steps = START, False, 0
        while not done and steps < 400:
            a = int(rng.integers(4)) if rng.random() < 0.1 else int(np.argmax(Q[s]))
            s2, r, done = step(s, a)
            counts[s2] += 1
            G.add_edge(s, s2)
            t += 1
            if bonus == "count":
                r += beta / np.sqrt(counts[s2])
            elif bonus == "se":
                if t % recluster == 0 and G.number_of_edges() > 4:
                    lab = se_optimize(G, seed=0)
                    labels = dict(zip(list(G.nodes()), lab))
                    # cluster visit counts CARRY OVER: derive from accumulated
                    # state counts (resetting re-pays stale novelty forever)
                    cl_counts = np.zeros(max(lab) + 1)
                    for node, c in labels.items():
                        cl_counts[c] += counts[node]
                if labels:
                    c = labels.get(s2)
                    if c is not None:
                        cl_counts[c] += 1
                        # state novelty + cluster novelty (the SI2E mechanism)
                        r += beta / np.sqrt(counts[s2]) + beta / np.sqrt(cl_counts[c])
                    else:
                        r += beta / np.sqrt(counts[s2])
                else:
                    r += beta / np.sqrt(counts[s2])
            best_next = 0.0 if done else Q[s2].max()
            Q[s][a] += 0.2 * (r + 0.97 * best_next - Q[s][a])
            s, steps = s2, steps + 1
        if done and solved_at is None:
            solved_at = ep
    # final greedy evaluation
    s, done, steps = START, False, 0
    while not done and steps < 400:
        s, _, done = step(s, int(np.argmax(Q[s])))
        steps += 1
    return solved_at if solved_at is not None else episodes, (steps if done else 400)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=300)
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    print(f"four-rooms {N}x{N}, sparse goal, {args.seeds} seeds, {args.episodes} episodes")
    print(f"{'bonus':8s} {'first-solve ep (mean+/-std)':30s} {'greedy path len':s}")
    for bonus in ("none", "count", "se"):
        firsts, lens = zip(*(run(bonus, args.episodes, s) for s in range(args.seeds)))
        print(f"{bonus:8s} {np.mean(firsts):7.1f} +/- {np.std(firsts):5.1f}{'':12s} "
              f"{np.mean(lens):6.1f}")


if __name__ == "__main__":
    main()
