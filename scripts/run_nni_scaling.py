"""Timing-only size sweep for released se_hier versus fast SE--NNI."""
import argparse
import json
import os
import sys
import time

import networkx as nx
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from selib.htree import encoding_tree, encoding_tree_nni_fast, hd_se


def graph_at_size(n, seed):
    if n % 8:
        raise ValueError("n must be divisible by 8")
    size = n // 8
    fine = np.repeat(np.arange(8), size)
    coarse = fine // 2
    rng = np.random.default_rng(seed)
    p_in = min(0.8, 8.0 / max(1, size - 1))
    p_mid = min(0.5, 2.0 / max(1, size))
    p_out = min(0.2, 1.0 / max(1, n - 2 * size))
    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    for u in range(n):
        for v in range(u + 1, n):
            p = p_in if fine[u] == fine[v] else (
                p_mid if coarse[u] == coarse[v] else p_out
            )
            if rng.random() < p:
                graph.add_edge(u, v, weight=1.0)
    components = [sorted(component) for component in nx.connected_components(graph)]
    for left, right in zip(components, components[1:]):
        graph.add_edge(left[0], right[0], weight=0.01)
    return graph


def run_method(build):
    start = time.perf_counter()
    root, _, _, vol = build()
    wall = time.perf_counter() - start
    return {"h": hd_se(root, vol), "time_s": wall}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="32,64,96,128")
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--output", default="results/nni_scaling.json")
    args = parser.parse_args()
    sizes = [int(value) for value in args.sizes.split(",")]
    records = []
    for n in sizes:
        for seed in range(args.seeds):
            graph = graph_at_size(n, seed)
            for method, build in [
                ("se_hier", lambda graph=graph, seed=seed: encoding_tree(
                    graph, seed=seed, starts=4, do_refine=True
                )),
                ("SE-NNI-fast", lambda graph=graph, seed=seed: encoding_tree_nni_fast(
                    graph, seed=seed, starts=4, compound=True
                )),
            ]:
                result = run_method(build)
                record = {
                    "n": n, "seed": seed, "method": method,
                    "m": graph.number_of_edges(), **result,
                }
                records.append(record)
                print(
                    f"[n={n} seed={seed}] {method} "
                    f"H={result['h']:.5f} t={result['time_s']:.3f}s",
                    flush=True,
                )
    with open(args.output, "w") as handle:
        json.dump({
            "protocol": {
                "sizes": sizes, "seeds": args.seeds,
                "timing": "wall clock without tracemalloc",
            },
            "records": records,
        }, handle, indent=2)
    print(f"WROTE {args.output} ({len(records)} records)")


if __name__ == "__main__":
    main()
