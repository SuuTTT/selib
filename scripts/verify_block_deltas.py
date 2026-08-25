#!/usr/bin/env python3
"""Mechanically verify exact Block-NEST-K deltas against full recomputation."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import networkx as nx

from selib.blockopt import exact_block_move
from selib.seopt import _State, _from_graph


def state_from(graph, labels):
    n, adjacency, degree, loops, volume, _, _ = _from_graph(graph)
    return _State(n, adjacency, degree, loops, volume, list(labels))


def random_graph(rng, n):
    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    for vertex in graph:
        if rng.random() < 0.2:
            graph.add_edge(vertex, vertex, weight=rng.uniform(0.01, 3.0))
    probability = rng.uniform(0.08, 0.55)
    for left in graph:
        for right in range(left + 1, n):
            if rng.random() < probability:
                graph.add_edge(left, right, weight=rng.uniform(0.01, 5.0))
    # The SE objective is undefined on a graph with zero total degree.
    if graph.size(weight="weight") == 0:
        graph.add_edge(0, 1, weight=1.0)
    return graph


def one_partition(rng, n, k):
    labels = [rng.randrange(k) for _ in range(n)]
    for community, vertex in enumerate(rng.sample(range(n), k)):
        labels[vertex] = community
    # Repair possible overwrites by borrowing from the largest community.
    for community in range(k):
        if community not in labels:
            donor = max(range(k), key=labels.count)
            labels[labels.index(donor)] = community
    return labels


def verify(trials, seed):
    rng = random.Random(seed)
    checked = 0
    maximum_error = 0.0
    started = time.perf_counter()
    while checked < trials:
        n = rng.randint(4, 22)
        k = rng.randint(2, min(6, n - 1))
        graph = random_graph(rng, n)
        labels = one_partition(rng, n, k)
        state = state_from(graph, labels)
        source = rng.randrange(k)
        members = [v for v, community in enumerate(labels) if community == source]
        if len(members) < 2:
            continue
        block_size = rng.randint(1, min(len(members) - 1, 6))
        block = tuple(rng.sample(members, block_size))
        target = rng.choice([community for community in range(k) if community != source])
        move = exact_block_move(state, block, target)
        changed = list(labels)
        for vertex in block:
            changed[vertex] = target
        rebuilt = state_from(graph, changed)
        error = abs((rebuilt.obj - state.obj) - move.delta)
        maximum_error = max(maximum_error, error)
        if error >= 1e-12:
            raise AssertionError({
                "trial": checked,
                "error": error,
                "n": n,
                "k": k,
                "block": block,
                "source": source,
                "target": target,
            })
        checked += 1
    return {
        "schema": "selib.block_delta_verification.v1",
        "seed": seed,
        "trials": checked,
        "maximum_absolute_error": maximum_error,
        "threshold": 1e-12,
        "passed": True,
        "wall_seconds": time.perf_counter() - started,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.trials, args.seed)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
        result["artifact_sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
