#!/usr/bin/env python3
"""Find a reproducible partition that is node-local but not block-local."""
from __future__ import annotations

import argparse
import itertools
import json
import random
from pathlib import Path

import networkx as nx

from selib.blockopt import exact_block_move
from selib.seopt import _State, _from_graph, _local_moves_fixed_k


def state_from(graph, labels):
    n, adjacency, degree, loops, volume, _, _ = _from_graph(graph)
    return _State(n, adjacency, degree, loops, volume, list(labels))


def node_certificate(state, tolerance=1e-12):
    best = 0.0
    for vertex in range(state.n):
        if state.size[state.comm[vertex]] <= 1:
            continue
        weights = state._w_to(vertex)
        source = state.comm[vertex]
        for target in state.V:
            if target == source:
                continue
            # Reuse the exact block formula on singleton proposals.
            best = min(best, exact_block_move(state, (vertex,), target).delta)
    return {"best_legal_node_delta": best, "certified": best >= -tolerance}


def search(seed, graphs, max_block_size):
    rng = random.Random(seed)
    for graph_index in range(graphs):
        n = rng.randint(7, 12)
        k = rng.randint(2, min(4, n - 2))
        graph = nx.Graph()
        graph.add_nodes_from(range(n))
        for left in range(n):
            for right in range(left + 1, n):
                if rng.random() < rng.uniform(0.18, 0.55):
                    graph.add_edge(left, right, weight=round(rng.uniform(0.05, 6.0), 6))
        if graph.number_of_edges() == 0:
            continue
        labels = [rng.randrange(k) for _ in range(n)]
        for community, vertex in enumerate(rng.sample(range(n), k)):
            labels[vertex] = community
        if len(set(labels)) != k:
            continue
        state = state_from(graph, labels)
        _local_moves_fixed_k(state, random.Random(seed + graph_index), max_passes=50)
        certificate = node_certificate(state)
        if not certificate["certified"]:
            continue

        best = None
        for source in sorted(state.V):
            members = [v for v, community in enumerate(state.comm) if community == source]
            for size in range(2, min(max_block_size, len(members) - 1) + 1):
                for block in itertools.combinations(members, size):
                    if not nx.is_connected(graph.subgraph(block)):
                        continue
                    for target in sorted(state.V):
                        if target == source:
                            continue
                        move = exact_block_move(state, block, target)
                        if best is None or move.delta < best.delta:
                            best = move
        if best is not None and best.delta < -1e-9:
            return {
                "schema": "selib.block_escape_witness.v1",
                "seed": seed,
                "graph_index": graph_index,
                "n": n,
                "k": k,
                "edges": [
                    [int(left), int(right), float(data["weight"])]
                    for left, right, data in graph.edges(data=True)
                ],
                "node_local_labels": list(state.comm),
                "node_certificate": certificate,
                "improving_block": list(best.block),
                "block_source": best.source,
                "block_target": best.target,
                "block_delta": best.delta,
                "objective_term": state.obj,
            }
    raise RuntimeError("no block-escape witness found within the search budget")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--graphs", type=int, default=20_000)
    parser.add_argument("--max-block-size", type=int, default=4)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = search(args.seed, args.graphs, args.max_block_size)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
