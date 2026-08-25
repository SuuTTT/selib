#!/usr/bin/env python3
"""Exhaustively check block deltas on deterministic small weighted graphs."""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

import networkx as nx

from selib.blockopt import exact_block_move
from selib.seopt import _State, _from_graph


def state_from(graph, labels):
    n, adjacency, degree, loops, volume, _, _ = _from_graph(graph)
    return _State(n, adjacency, degree, loops, volume, list(labels))


def weighted_graph(n):
    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    for vertex in range(n):
        if vertex % 3 == 0:
            graph.add_edge(vertex, vertex, weight=(vertex + 1) / 17.0)
    for left in range(n):
        for right in range(left + 1, n):
            # A deterministic mix of present/absent non-integral weights.
            code = (left * 11 + right * 7 + n * 5) % 9
            if code not in (0, 4):
                graph.add_edge(left, right, weight=(code + 1) / 13.0)
    return graph


def canonical_surjections(n, k):
    # Fix vertex zero to community zero to remove global label permutations.
    for tail in itertools.product(range(k), repeat=n - 1):
        labels = (0,) + tail
        if len(set(labels)) == k:
            yield labels


def verify(max_n, max_k):
    maximum_error = 0.0
    checks = 0
    cases = []
    started = time.perf_counter()
    for n in range(2, max_n + 1):
        graph = weighted_graph(n)
        # K=2 is exhaustive through n=10. K=3 is also exhaustive through n=8
        # by default, keeping this audit bounded and reproducible.
        n_max_k = min(max_k, n - 1, 3 if n <= 8 else 2)
        for k in range(2, n_max_k + 1):
            case_checks = 0
            partitions = 0
            for labels in canonical_surjections(n, k):
                partitions += 1
                state = state_from(graph, labels)
                for source in range(k):
                    members = [v for v, c in enumerate(labels) if c == source]
                    for size in range(1, len(members)):
                        for block in itertools.combinations(members, size):
                            for target in range(k):
                                if target == source:
                                    continue
                                move = exact_block_move(state, block, target)
                                changed = list(labels)
                                for vertex in block:
                                    changed[vertex] = target
                                rebuilt = state_from(graph, changed)
                                error = abs((rebuilt.obj - state.obj) - move.delta)
                                maximum_error = max(maximum_error, error)
                                if error >= 1e-12:
                                    raise AssertionError({
                                        "n": n, "k": k, "labels": labels,
                                        "block": block, "target": target,
                                        "error": error,
                                    })
                                checks += 1
                                case_checks += 1
            cases.append({
                "n": n,
                "k": k,
                "partitions": partitions,
                "moves": case_checks,
            })
    return {
        "schema": "selib.block_delta_exhaustive.v1",
        "max_n": max_n,
        "max_k": max_k,
        "coverage": "all canonical K=2 partitions/moves through n=10; K=3 through n=8",
        "cases": cases,
        "moves": checks,
        "maximum_absolute_error": maximum_error,
        "threshold": 1e-12,
        "passed": True,
        "wall_seconds": time.perf_counter() - started,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-n", type=int, default=10)
    parser.add_argument("--max-k", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.max_n, args.max_k)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
