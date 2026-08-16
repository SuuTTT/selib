#!/usr/bin/env python3
"""Small, no-download release gate for selib's native SE algorithms.

This script is deliberately a regression benchmark, not a paper leaderboard.
It writes raw seed-level records so its summary can always be recomputed.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import networkx as nx
import selib
from selib import datasets as D
from selib import metrics as M
from selib.htree import encoding_tree, encoding_tree_nni, encoding_tree_nni_fast, hd_se
from selib.seopt import se_optimize_fixed_k


def _datasets():
    return [
        ("Karate", D.karate, None),
        ("SBM-Clean", lambda: D.sbm(64, 3, 0.30, 0.05, seed=11), 3),
        ("SBM-Moderate", lambda: D.sbm(64, 3, 0.20, 0.07, seed=12), 3),
        ("SBM-Noisy", lambda: D.sbm(64, 3, 0.15, 0.08, seed=13), 3),
    ]


def _flat_methods(known_k):
    methods = [("louvain", lambda graph, seed: selib.get("louvain").fit_predict(graph, seed=seed), "free-K")]
    methods.append(("se_louvain", lambda graph, seed: selib.se_optimize(graph, seed=seed), "free-K"))
    if known_k is not None:
        methods.extend([
            ("spectral", lambda graph, seed: selib.get("spectral").fit_predict(graph, k=known_k, seed=seed), "known-K"),
            ("se_fixed_k", lambda graph, seed: se_optimize_fixed_k(graph, k=known_k, seed=seed), "known-K"),
        ])
    return methods


def _summary(records):
    grouped = {}
    for row in records:
        key = (row["block"], row["dataset"], row["method"], row["condition"])
        grouped.setdefault(key, []).append(row)
    output = []
    for key, rows in sorted(grouped.items()):
        block, dataset, method, condition = key
        result = {"block": block, "dataset": dataset, "method": method, "condition": condition,
                  "runs": len(rows)}
        for metric in ("ari", "nmi", "structural_entropy_2d", "tree_entropy", "time_s", "num_modules"):
            values = [r[metric] for r in rows if metric in r]
            if values:
                result[f"mean_{metric}"] = sum(values) / len(values)
        output.append(result)
    return output


def run(seeds):
    records = []
    for name, loader, declared_k in _datasets():
        graph, truth = loader()
        graph = nx.convert_node_labels_to_integers(graph)
        for method, fit, condition in _flat_methods(declared_k):
            for seed in seeds:
                started = time.perf_counter()
                labels = fit(graph, seed)
                elapsed = time.perf_counter() - started
                records.append({
                    "block": "flat", "dataset": name, "method": method,
                    "condition": condition, "seed": seed,
                    "n": graph.number_of_nodes(), "m": graph.number_of_edges(),
                    "ari": M.ari(truth, labels), "nmi": M.nmi(truth, labels),
                    "structural_entropy_2d": M.structural_entropy_2d(graph, labels),
                    "num_modules": len(set(labels)), "time_s": elapsed,
                })
        for method, build in [
            ("se_hier", encoding_tree),
            ("se_hier_nni", encoding_tree_nni),
            ("se_nni_fast", encoding_tree_nni_fast),
        ]:
            for seed in seeds:
                started = time.perf_counter()
                tree, _, _, volume = build(graph, seed=seed)
                elapsed = time.perf_counter() - started
                records.append({
                    "block": "tree", "dataset": name, "method": method,
                    "condition": "unsupervised", "seed": seed,
                    "n": graph.number_of_nodes(), "m": graph.number_of_edges(),
                    "tree_entropy": hd_se(tree, volume), "time_s": elapsed,
                })
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--output", type=Path, default=Path("results/core_benchmark.json"))
    args = parser.parse_args()
    records = run(args.seeds)
    payload = {
        "protocol": "docs/RELEASE_BENCHMARK.md",
        "selib_version": selib.__version__,
        "python": sys.version,
        "platform": platform.platform(),
        "seeds": args.seeds,
        "records": records,
        "summary": _summary(records),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {args.output} ({len(records)} seed-level records)")


if __name__ == "__main__":
    main()
