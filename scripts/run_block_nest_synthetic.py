#!/usr/bin/env python3
"""Label-isolated synthetic mechanism screen for Block-NEST-K."""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import networkx as nx
import numpy as np
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from selib.block_proposals import (
    agreement_blocks,
    deduplicate_blocks,
    induced_component_blocks,
)
from selib.blockopt import (
    refine_pairwise_merge_split_fixed_k,
    se_optimize_block_fixed_k,
)
from selib.metrics import structural_entropy_2d
from selib.seopt import _spectral_seed_labels, se_optimize_fixed_k


SIGNALS = {"weak": 0.58, "medium": 0.76, "strong": 0.91}


def balanced_labels(n, k):
    return np.arange(n, dtype=int) % k


def severe_labels(n, k):
    weights = np.arange(k, 0, -1, dtype=float) ** 2
    counts = np.maximum(1, np.floor(n * weights / weights.sum()).astype(int))
    counts[0] += n - int(counts.sum())
    return np.concatenate([np.full(count, community) for community, count in enumerate(counts)])


def make_labels(n, k, balance, rng):
    labels = balanced_labels(n, k) if balance == "balanced" else severe_labels(n, k)
    rng.shuffle(labels)
    return labels


def sample_view(labels, homophily, fragmentation, mean_degree, rng, powerlaw=False):
    n = len(labels)
    k = int(labels.max()) + 1
    fragments = (np.arange(n) * 104729 + labels * 8191) % max(2, k)
    by_class = [np.flatnonzero(labels == community) for community in range(k)]
    by_fragment = {}
    for community in range(k):
        for fragment in range(max(2, k)):
            by_fragment[(community, fragment)] = np.flatnonzero(
                (labels == community) & (fragments == fragment)
            )
    graph = nx.Graph()
    graph.add_nodes_from(range(n))
    for vertex in range(n):
        degree = mean_degree
        if powerlaw:
            degree = min(int(mean_degree * 4), max(2, int(rng.zipf(2.4))))
        for _ in range(degree):
            same = rng.random() < homophily
            if same:
                pool = by_class[int(labels[vertex])]
                if rng.random() < fragmentation:
                    local = by_fragment[(int(labels[vertex]), int(fragments[vertex]))]
                    if len(local) > 1:
                        pool = local
            else:
                other = rng.integers(0, k - 1)
                if other >= labels[vertex]:
                    other += 1
                pool = by_class[int(other)]
            if len(pool) == 0:
                continue
            neighbor = int(pool[rng.integers(0, len(pool))])
            if neighbor != vertex:
                graph.add_edge(vertex, neighbor, weight=1.0)
    return graph


def normalized_fusion(topology, feature):
    fused = nx.Graph()
    fused.add_nodes_from(topology.nodes())
    top_mass = max(topology.size(weight="weight"), 1.0)
    feature_mass = max(feature.size(weight="weight"), 1.0)
    for graph, mass in ((topology, top_mass), (feature, feature_mass)):
        for left, right, data in graph.edges(data=True):
            weight = float(data.get("weight", 1.0)) / mass
            if fused.has_edge(left, right):
                fused[left][right]["weight"] += weight
            else:
                fused.add_edge(left, right, weight=weight)
    return fused


def condition(args, topology_signal, feature_signal, alignment, fragmentation, seed):
    rng = np.random.default_rng(seed)
    truth = make_labels(args.n, args.k, args.balance, rng)
    independent = make_labels(args.n, args.k, args.balance, rng)
    if alignment == "aligned":
        topology_labels, feature_labels = truth, truth
    elif alignment == "topology_only":
        topology_labels, feature_labels = truth, independent
        feature_signal = "weak"
    elif alignment == "feature_only":
        topology_labels, feature_labels = independent, truth
        topology_signal = "weak"
    elif alignment == "conflict":
        topology_labels, feature_labels = independent, truth
    else:
        raise ValueError(alignment)
    topology = sample_view(
        topology_labels, SIGNALS[topology_signal], fragmentation,
        args.mean_degree, rng, args.degree == "powerlaw",
    )
    feature = sample_view(
        feature_labels, SIGNALS[feature_signal], 0.0,
        args.mean_degree, rng, args.degree == "powerlaw",
    )
    fused = normalized_fusion(topology, feature)

    preprocess_started = time.perf_counter()
    top_seed = _spectral_seed_labels(topology, args.k, seed)
    feature_seed = _spectral_seed_labels(feature, args.k, seed)
    fused_seed = _spectral_seed_labels(fused, args.k, seed)
    proposals = deduplicate_blocks(
        agreement_blocks([top_seed, feature_seed, fused_seed])
        + induced_component_blocks(topology, fused_seed)
    )
    preprocess_seconds = time.perf_counter() - preprocess_started

    started = time.perf_counter()
    sparse = se_optimize_fixed_k(
        fused, args.k, starts=args.starts, max_passes=args.node_passes,
        seed=seed, spectral_init=True,
    )
    sparse_seconds = time.perf_counter() - started
    initial_partitions = [sparse, top_seed, feature_seed, fused_seed]
    started = time.perf_counter()
    diverse, diverse_audit = se_optimize_block_fixed_k(
        fused,
        args.k,
        blocks=[],
        initial_partitions=initial_partitions,
        starts=args.starts,
        max_node_passes=args.node_passes,
        max_block_passes=args.block_passes,
        seed=seed,
        return_audit=True,
    )
    diverse_extension_seconds = time.perf_counter() - started
    started = time.perf_counter()
    block, audit = se_optimize_block_fixed_k(
        fused,
        args.k,
        proposals,
        initial_partitions=initial_partitions,
        starts=args.starts,
        max_node_passes=args.node_passes,
        max_block_passes=args.block_passes,
        seed=seed,
        return_audit=True,
    )
    block_extension_seconds = time.perf_counter() - started
    diverse_seconds = preprocess_seconds + sparse_seconds + diverse_extension_seconds
    block_seconds = preprocess_seconds + sparse_seconds + block_extension_seconds
    started = time.perf_counter()
    merge_split, merge_split_audit = refine_pairwise_merge_split_fixed_k(
        fused,
        block,
        split_graphs=[topology, feature],
        max_passes=args.merge_split_passes,
        pair_node_passes=args.node_passes,
        seed=seed,
    )
    merge_split_extension_seconds = time.perf_counter() - started
    merge_split_seconds = block_seconds + merge_split_extension_seconds

    def report(labels):
        return {
            "h2": structural_entropy_2d(fused, labels),
            "nmi": normalized_mutual_info_score(truth, labels),
            "ari": adjusted_rand_score(truth, labels),
            "k": len(set(labels)),
        }

    sparse_result = report(sparse)
    diverse_result = report(diverse)
    block_result = report(block)
    merge_split_result = report(merge_split)
    best_run = audit["runs"][audit["best_restart"]]
    accepted_blocks = sum(
        record["accepted_block_moves"] for record in best_run["cycles"]
    ) + len(best_run["final_block_scan"]["accepted_moves"])
    return {
        "config": {
            "n": args.n, "k": args.k, "topology_signal": topology_signal,
            "feature_signal": feature_signal, "alignment": alignment,
            "fragmentation": fragmentation, "degree": args.degree,
            "balance": args.balance, "seed": seed,
        },
        "graph": {
            "topology_edges": topology.number_of_edges(),
            "feature_edges": feature.number_of_edges(),
            "fused_edges": fused.number_of_edges(),
            "proposal_count": len(proposals),
        },
        "sparse_init_nest": {**sparse_result, "wall_seconds": sparse_seconds},
        "view_diverse_node": {
            **diverse_result,
            "wall_seconds": diverse_seconds,
            "best_joint_certificate": diverse_audit["best_joint_certificate"],
        },
        "block_nest_k": {
            **block_result,
            "wall_seconds": block_seconds,
            "best_joint_certificate": audit["best_joint_certificate"],
            "accepted_block_moves_in_best_restart": accepted_blocks,
        },
        "block_nest_k_merge_split": {
            **merge_split_result,
            "wall_seconds": merge_split_seconds,
            "accepted_merge_splits": len(merge_split_audit["accepted_moves"]),
            "certified_pairwise_local": merge_split_audit["certified_pairwise_local"],
        },
        "delta": {
            "block_vs_sparse_h2": block_result["h2"] - sparse_result["h2"],
            "block_vs_sparse_nmi": block_result["nmi"] - sparse_result["nmi"],
            "block_vs_sparse_ari": block_result["ari"] - sparse_result["ari"],
            "block_vs_diverse_h2": block_result["h2"] - diverse_result["h2"],
            "block_vs_diverse_nmi": block_result["nmi"] - diverse_result["nmi"],
            "block_vs_diverse_ari": block_result["ari"] - diverse_result["ari"],
            "merge_split_vs_block_h2": merge_split_result["h2"] - block_result["h2"],
            "merge_split_vs_block_nmi": merge_split_result["nmi"] - block_result["nmi"],
            "merge_split_vs_block_ari": merge_split_result["ari"] - block_result["ari"],
            "wall_ratio": merge_split_seconds / max(sparse_seconds, 1e-12),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--signals", nargs="+", default=["weak", "strong"])
    parser.add_argument("--alignments", nargs="+", default=["aligned", "feature_only", "conflict"])
    parser.add_argument("--fragmentations", nargs="+", type=float, default=[0.0, 0.5, 0.75])
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--degree", choices=["homogeneous", "powerlaw"], default="homogeneous")
    parser.add_argument("--balance", choices=["balanced", "severe"], default="balanced")
    parser.add_argument("--mean-degree", type=int, default=10)
    parser.add_argument("--starts", type=int, default=4)
    parser.add_argument("--node-passes", type=int, default=20)
    parser.add_argument("--block-passes", type=int, default=10)
    parser.add_argument("--merge-split-passes", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = []
    for topology_signal in args.signals:
        for feature_signal in args.signals:
            for alignment in args.alignments:
                for fragmentation in args.fragmentations:
                    for seed in args.seeds:
                        result = condition(
                            args, topology_signal, feature_signal, alignment,
                            fragmentation, seed,
                        )
                        results.append(result)
                        print(json.dumps(result), flush=True)
    payload = {
        "schema": "selib.block_nest_synthetic.v1",
        "selection_uses_truth": False,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
