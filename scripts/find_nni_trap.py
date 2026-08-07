"""Search deterministic small weighted graphs for a strict one-NNI trap.

The output is a reproducible witness where exact one-step NNI descent stalls
but bounded two-step lookahead lowers tree structural entropy.
"""
import json
import random

import networkx as nx

from selib.htree import (
    TNode,
    _graph_arrays,
    annotate,
    hd_se,
    refine_nni,
    refine_nni_compound,
)


def random_binary_tree(n, rng):
    forest = [TNode(vertex=i) for i in range(n)]
    while len(forest) > 1:
        first, second = sorted(rng.sample(range(len(forest)), 2), reverse=True)
        left = forest.pop(first)
        right = forest.pop(second)
        forest.append(TNode(children=[left, right]))
    return forest[0]


def main():
    for seed in range(2000):
        rng = random.Random(seed)
        n = 7 + seed % 5
        graph = nx.gnp_random_graph(n, 0.38, seed=seed)
        for node in range(n - 1):
            graph.add_edge(node, node + 1)
        for u, v in graph.edges():
            graph[u][v]["weight"] = round(0.2 + 2.8 * rng.random(), 6)

        root = random_binary_tree(n, rng)
        _, _, _, adj, deg, vol = _graph_arrays(graph)
        annotate(root, deg, adj, vol)
        local = refine_nni(root, deg, adj, vol)
        annotate(local, deg, adj, vol)
        local_h = hd_se(local, vol)
        escaped, trace = refine_nni_compound(
            local, deg, adj, vol,
            max_rounds=2,
            beam_width=32,
            barrier_bits=0.25,
            return_trace=True,
        )
        annotate(escaped, deg, adj, vol)
        escaped_h = hd_se(escaped, vol)
        compound = [step for step in trace if step["kind"] == "compound"]
        if escaped_h < local_h - 1e-9 and compound:
            witness = {
                "seed": seed,
                "n": n,
                "edges": [
                    [u, v, data["weight"]]
                    for u, v, data in graph.edges(data=True)
                ],
                "one_nni_local_h": local_h,
                "compound_h": escaped_h,
                "gain": local_h - escaped_h,
                "compound_trace": compound,
            }
            print(json.dumps(witness, indent=2))
            return
    raise SystemExit("no witness found")


if __name__ == "__main__":
    main()
