"""Exact global-optimum audit of NEST on small hierarchical graphs."""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

import networkx as nx
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from selib.htree import encoding_tree_nni_fast, hd_se
from selib.optimality import edge_lca_lower_bound, exact_tree_entropy


REGIMES = {
    "clean": ((0.72, 0.25, 0.04), [2, 2, 2, 2, 2, 2]),
    "noisy": ((0.50, 0.30, 0.14), [2, 2, 2, 2, 2, 2]),
    "imbalanced": ((0.65, 0.23, 0.06), [1, 3, 1, 3, 2, 2]),
    "weighted": ((0.60, 0.22, 0.06), [2, 2, 2, 2, 2, 2]),
    "weak-hierarchy": ((0.45, 0.36, 0.10), [2, 2, 2, 2, 2, 2]),
}


def small_hierarchical_sbm(regime, seed):
    probabilities, sizes = REGIMES[regime]
    rng = np.random.default_rng(seed)
    fine, coarse = [], []
    for block, size in enumerate(sizes):
        fine.extend([block] * size)
        coarse.extend([block // 2] * size)
    graph = nx.Graph()
    graph.add_nodes_from(range(len(fine)))
    for u in graph:
        for v in range(u + 1, len(fine)):
            probability = (
                probabilities[0] if fine[u] == fine[v]
                else probabilities[1] if coarse[u] == coarse[v]
                else probabilities[2]
            )
            if rng.random() < probability:
                if regime == "weighted":
                    scale = (
                        2.0 if fine[u] == fine[v]
                        else 1.0 if coarse[u] == coarse[v]
                        else 0.5
                    )
                    weight = float(scale * rng.lognormal(0.0, 0.25))
                else:
                    weight = 1.0
                graph.add_edge(u, v, weight=weight)

    connectors = []
    components = [sorted(part) for part in nx.connected_components(graph)]
    for left, right in zip(components, components[1:]):
        graph.add_edge(left[0], right[0], weight=0.01)
        connectors.append([left[0], right[0], 0.01])
    manifest = {
        "regime": regime,
        "sizes": sizes,
        "probabilities": probabilities,
        "connectors": connectors,
    }
    return graph, manifest


def summarize(records):
    output = {}
    for regime in [*REGIMES, "overall"]:
        rows = records if regime == "overall" else [
            row for row in records if row["regime"] == regime
        ]
        output[regime] = {
            "runs": len(rows),
            "globally_optimal": sum(row["globally_optimal"] for row in rows),
            "mean_additive_gap_bits": float(np.mean([
                row["additive_gap_bits"] for row in rows
            ])),
            "max_additive_gap_bits": float(np.max([
                row["additive_gap_bits"] for row in rows
            ])),
            "mean_relative_gap_percent": float(np.mean([
                row["relative_gap_percent"] for row in rows
            ])),
            "max_relative_gap_percent": float(np.max([
                row["relative_gap_percent"] for row in rows
            ])),
        }
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/nni_optimality.json")
    parser.add_argument("--seeds", type=int, default=10)
    args = parser.parse_args()

    records = []
    started = time.time()
    for regime in REGIMES:
        for seed in range(args.seeds):
            graph, manifest = small_hierarchical_sbm(regime, seed)
            exact_started = time.perf_counter()
            optimum = exact_tree_entropy(graph, max_nodes=12)
            exact_time = time.perf_counter() - exact_started
            nest_started = time.perf_counter()
            root, _, _, volume = encoding_tree_nni_fast(graph, seed=seed)
            nest_entropy = hd_se(root, volume)
            nest_time = time.perf_counter() - nest_started
            gap = max(0.0, nest_entropy - optimum)
            relative = 100.0 * gap / optimum if optimum > 0 else 0.0
            record = {
                "regime": regime,
                "seed": seed,
                "n": len(graph),
                "m": graph.number_of_edges(),
                "manifest": manifest,
                "global_optimum_bits": optimum,
                "nest_entropy_bits": nest_entropy,
                "additive_gap_bits": gap,
                "relative_gap_percent": relative,
                "globally_optimal": gap <= 1e-9,
                "edge_lca_lower_bound_bits": edge_lca_lower_bound(graph),
                "exact_time_s": exact_time,
                "nest_time_s": nest_time,
            }
            records.append(record)
            print(
                f"{regime:14s} seed={seed} exact={optimum:.6f} "
                f"NEST={nest_entropy:.6f} gap={relative:.3f}%",
                flush=True,
            )

    artifact = {
        "protocol": {
            "version": "tamc-nest-exact-v1",
            "purpose": "exact global-optimum audit; no model selection",
            "graph_family": "six-fine-block, three-coarse-block HSBM",
            "n": 12,
            "seeds_per_regime": args.seeds,
            "regimes": REGIMES,
            "optimizer": "exact unordered-subset DP over binary trees",
            "complexity": "O(3^n) time and O(2^n) memory",
            "nest": {
                "compound_rounds": 8,
                "beam_width": 16,
                "barrier_bits": 0.05,
            },
        },
        "environment": {
            "python": platform.python_version(),
            "networkx": nx.__version__,
            "numpy": np.__version__,
        },
        "records": records,
        "summary": summarize(records),
        "elapsed_s": time.time() - started,
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n")


if __name__ == "__main__":
    main()
