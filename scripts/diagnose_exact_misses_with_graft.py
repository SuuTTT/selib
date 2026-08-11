#!/usr/bin/env python3
"""Reconstruct the five sealed NEST misses and test full-rescore graft search.

The exact optimum is used only after each hierarchy has been selected.  Graph
and restart seeds are copied from the sealed n=12, n=14, and n=16 artifacts.
This diagnostic does not modify those artifacts.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random
import time

import networkx as nx
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "_selib_htree_graft_diagnostic", REPO_ROOT / "selib" / "htree.py"
)
assert SPEC is not None and SPEC.loader is not None
HTREE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HTREE)

REGIMES = {
    "clean": (0.72, 0.25, 0.04),
    "noisy": (0.50, 0.30, 0.14),
    "imbalanced": (0.65, 0.23, 0.06),
    "weighted": (0.60, 0.22, 0.06),
    "weak-hierarchy": (0.45, 0.36, 0.10),
}

MISSES = [
    {
        "n": 12, "regime": "clean", "graph_seed": 168,
        "sizes": [2, 2, 2, 2, 2, 2],
        "restart_seed": 202608100000168,
        "optimum_bits": 1.656298994142502,
    },
    {
        "n": 14, "regime": "weak-hierarchy", "graph_seed": 3004,
        "sizes": [3, 3, 2, 2, 2, 2],
        "restart_seed": 202608120403004,
        "optimum_bits": 2.023108297936261,
    },
    {
        "n": 16, "regime": "noisy", "graph_seed": 4001,
        "sizes": [3, 3, 3, 3, 2, 2],
        "restart_seed": 202608130104001,
        "optimum_bits": 2.273864438329438,
    },
    {
        "n": 16, "regime": "noisy", "graph_seed": 4002,
        "sizes": [3, 3, 3, 3, 2, 2],
        "restart_seed": 202608130104002,
        "optimum_bits": 2.2790598389951193,
    },
    {
        "n": 16, "regime": "weak-hierarchy", "graph_seed": 4002,
        "sizes": [3, 3, 3, 3, 2, 2],
        "restart_seed": 202608130404002,
        "optimum_bits": 2.293390642473512,
    },
]


def generate_graph(regime: str, seed: int, sizes: list[int]) -> nx.Graph:
    probabilities = REGIMES[regime]
    regime_index = list(REGIMES).index(regime)
    rng = np.random.default_rng(seed + 1_000_003 * (regime_index + 1))
    fine = []
    coarse = []
    for block, size in enumerate(sizes):
        fine.extend([block] * size)
        coarse.extend([block // 2] * size)
    graph = nx.Graph()
    graph.add_nodes_from(range(len(fine)))
    for left in graph:
        for right in range(left + 1, len(fine)):
            probability = (
                probabilities[0] if fine[left] == fine[right]
                else probabilities[1] if coarse[left] == coarse[right]
                else probabilities[2]
            )
            if rng.random() < probability:
                graph.add_edge(left, right, weight=1.0)
    components = [sorted(part) for part in nx.connected_components(graph)]
    for left, right in zip(components, components[1:]):
        graph.add_edge(left[0], right[0], weight=0.01)
    return graph


def is_exact(value: float, optimum: float) -> bool:
    return abs(value - optimum) <= max(1e-9, 1e-9 * abs(optimum))


def diagnose(case: dict) -> dict:
    graph = generate_graph(case["regime"], case["graph_seed"], case["sizes"])
    assert len(graph) == case["n"]
    _, _, _, adjacency, degrees, volume = HTREE._graph_arrays(graph)
    rng = random.Random(case["restart_seed"])
    records = []
    started = time.perf_counter()

    for restart in range(32):
        root = HTREE.random_coalescent_tree(case["n"], rng)
        HTREE.annotate(root, degrees, adjacency, volume)
        root = HTREE.refine_nni(root, degrees, adjacency, volume)
        root = HTREE.refine_nni_compound(
            root, degrees, adjacency, volume,
            max_rounds=8, beam_width=16, barrier_bits=0.05,
        )
        HTREE.annotate(root, degrees, adjacency, volume)
        before = HTREE.hd_se(root, volume)
        grafted, trace = HTREE.refine_graft(
            root, degrees, adjacency, volume,
            max_rounds=100, post_nni=True, return_trace=True,
        )
        HTREE.annotate(grafted, degrees, adjacency, volume)
        after = HTREE.hd_se(grafted, volume)
        records.append({
            "restart": restart,
            "before_bits": before,
            "after_graft_bits": after,
            "graft_improvement_bits": before - after,
            "accepted_grafts": sum(
                step["kind"] == "graft" for step in trace
            ),
        })

    best_before = min(row["before_bits"] for row in records)
    best_after = min(row["after_graft_bits"] for row in records)
    optimum = case["optimum_bits"]
    return {
        **case,
        "m": graph.number_of_edges(),
        "reconstructed_best_before_bits": best_before,
        "best_after_graft_bits": best_after,
        "gap_before_bits": max(0.0, best_before - optimum),
        "gap_after_graft_bits": max(0.0, best_after - optimum),
        "exact_before": is_exact(best_before, optimum),
        "exact_after_graft": is_exact(best_after, optimum),
        "restarts_improved_by_graft": sum(
            row["after_graft_bits"] < row["before_bits"] - 1e-10
            for row in records
        ),
        "elapsed_s": time.perf_counter() - started,
        "restarts": records,
    }


def main() -> None:
    started = time.perf_counter()
    cases = []
    for case in MISSES:
        result = diagnose(case)
        cases.append(result)
        print(
            f"{case['regime']} n={case['n']} seed={case['graph_seed']}: "
            f"{result['gap_before_bits']:.12g} -> "
            f"{result['gap_after_graft_bits']:.12g} bits",
            flush=True,
        )
    artifact = {
        "protocol": {
            "cases": "five misses declared by sealed n=12/n=14/n=16 audits",
            "candidate_budget": 32,
            "initializer": "pairwise random coalescent",
            "baseline_refinement": "exact one-NNI descent plus bounded two-step search",
            "extension": "best-improvement full-rescore rooted subtree graft; exact NNI after each accepted graft",
            "selection": "structural entropy only; exact optimum consulted after selection",
        },
        "cases": cases,
        "summary": {
            "cases": len(cases),
            "exact_before": sum(case["exact_before"] for case in cases),
            "exact_after_graft": sum(case["exact_after_graft"] for case in cases),
            "elapsed_s": time.perf_counter() - started,
        },
    }
    output = REPO_ROOT / "results" / "tcs_graft_exact_miss_diagnostic.json"
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    print(json.dumps(artifact["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
