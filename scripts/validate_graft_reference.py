#!/usr/bin/env python3
"""Deterministic validation for the correctness-first graft implementation.

This intentionally avoids pytest so it can run in the project's minimal
Python environment.  It checks topology preservation for every enumerated
move and verifies monotonicity plus exhaustive graft-local termination on a
small weighted-graph suite.
"""
from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import random

import networkx as nx

# Load the module directly so validation does not import every optional package
# re-exported by ``selib.__init__``.
MODULE_PATH = Path(__file__).resolve().parents[1] / "selib" / "htree.py"
SPEC = importlib.util.spec_from_file_location("_selib_htree_reference", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
HTREE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HTREE)

TNode = HTREE.TNode
_do_graft = HTREE._do_graft
_graft_candidates = HTREE._graft_candidates
_graph_arrays = HTREE._graph_arrays
annotate = HTREE.annotate
hd_se = HTREE.hd_se
graft_delta = HTREE.graft_delta
refine_graft = HTREE.refine_graft


def random_tree(n: int, seed: int) -> TNode:
    rng = random.Random(seed)
    forest = [TNode(vertex=i) for i in range(n)]
    while len(forest) > 1:
        first, second = sorted(rng.sample(range(len(forest)), 2), reverse=True)
        left = forest.pop(first)
        right = forest.pop(second)
        forest.append(TNode(children=[left, right]))
    return forest[0]


def weighted_graph(n: int, seed: int) -> nx.Graph:
    rng = random.Random(seed)
    graph = nx.gnp_random_graph(n, 0.45, seed=seed)
    for node in range(n - 1):
        graph.add_edge(node, node + 1)
    for left, right in graph.edges():
        graph[left][right]["weight"] = 0.1 + 2.0 * rng.random()
    return graph


def assert_binary_leaf_bijection(root: TNode, n: int) -> None:
    leaves = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.is_leaf():
            leaves.append(node.vertex)
        else:
            assert len(node.children) == 2
            stack.extend(node.children)
    assert sorted(leaves) == list(range(n))


def main() -> None:
    topology_moves = 0
    max_delta_error = 0.0
    for seed in range(20):
        n = 5 + seed % 5
        root = random_tree(n, 1000 + seed)
        graph = weighted_graph(n, 4000 + seed)
        _, _, _, adjacency, degrees, volume = _graph_arrays(graph)
        annotate(root, degrees, adjacency, volume)
        before = hd_se(root, volume)
        for source_path, target_path in _graft_candidates(root):
            candidate = _do_graft(root, source_path, target_path)
            assert candidate is not None
            assert_binary_leaf_bijection(candidate, n)
            predicted = graft_delta(
                root, source_path, target_path, adjacency, degrees, volume
            )
            annotate(candidate, degrees, adjacency, volume)
            observed = hd_se(candidate, volume) - before
            max_delta_error = max(max_delta_error, abs(predicted - observed))
            assert abs(predicted - observed) < 1e-9, {
                "seed": seed,
                "source_path": source_path,
                "target_path": target_path,
                "predicted": predicted,
                "observed": observed,
            }
            topology_moves += 1

    optimization_cases = []
    for seed in range(4):
        n = 7 + seed % 2
        graph = weighted_graph(n, 2000 + seed)
        root = random_tree(n, 3000 + seed)
        _, _, _, adj, deg, volume = _graph_arrays(graph)
        annotate(root, deg, adj, volume)
        before = hd_se(root, volume)
        refined, trace = refine_graft(
            root, deg, adj, volume, max_rounds=100,
            post_nni=True, return_trace=True,
        )
        annotate(refined, deg, adj, volume)
        after = hd_se(refined, volume)
        assert after <= before + 1e-10
        assert all(
            step["after"] < step["before"]
            for step in trace if step["kind"] == "graft"
        )
        final_candidates = _graft_candidates(refined)
        for source_path, target_path in final_candidates:
            candidate = _do_graft(refined, source_path, target_path)
            assert candidate is not None
            annotate(candidate, deg, adj, volume)
            assert hd_se(candidate, volume) >= after - 1e-10
        optimization_cases.append({
            "seed": seed,
            "n": n,
            "before_bits": before,
            "after_bits": after,
            "accepted_grafts": sum(
                step["kind"] == "graft" for step in trace
            ),
            "certified_candidates": len(final_candidates),
        })

    print(json.dumps({
        "max_graft_delta_error": max_delta_error,
        "topology_moves_checked": topology_moves,
        "optimization_cases": optimization_cases,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
