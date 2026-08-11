"""Search regular graph families for unbalanced optimal two-module SE splits.

This tests whether the balance constraint in the Minimum-Bisection identity can
be dropped for free. A counterexample means a hardness proof needs a forcing
gadget or a different source problem.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from check_balanced_se_bisection import canonical_entropy, cut_weight, graph_suite


def bipartitions(n: int):
    """Yield every unordered nontrivial bipartition once, with vertex 0 on side 0."""
    for bits in range(1 << (n - 1)):
        labels = [0]
        labels.extend(1 if bits & (1 << offset) else 0 for offset in range(n - 1))
        if all(label == 0 for label in labels):
            continue
        yield labels


def analyze_graph(name, n, edges):
    all_records = []
    balanced_records = []
    for labels in bipartitions(n):
        side_one = sum(labels)
        smaller_side = min(side_one, n - side_one)
        record = {
            "entropy": canonical_entropy(n, edges, labels),
            "cut": cut_weight(edges, labels),
            "smaller_side": smaller_side,
        }
        all_records.append(record)
        if side_one == n // 2:
            balanced_records.append(record)

    best = min(row["entropy"] for row in all_records)
    best_balanced = min(row["entropy"] for row in balanced_records)
    optimal = [row for row in all_records if abs(row["entropy"] - best) <= 1e-12]
    return {
        "name": name,
        "n": n,
        "partitions": len(all_records),
        "optimal_entropy_bits": best,
        "balanced_optimal_entropy_bits": best_balanced,
        "balanced_minus_unconstrained_bits": best_balanced - best,
        "optimal_smaller_side_sizes": sorted({row["smaller_side"] for row in optimal}),
        "optimal_cut_weights": sorted({row["cut"] for row in optimal}),
        "has_balanced_global_optimum": any(
            row["smaller_side"] == n // 2 for row in optimal
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    records = [analyze_graph(name, n, edges) for name, n, edges in graph_suite()]
    counterexamples = [row for row in records if not row["has_balanced_global_optimum"]]
    summary = {
        "protocol": "unconstrained-two-module-se-balance-check-v1",
        "graphs": len(records),
        "partitions": sum(row["partitions"] for row in records),
        "graphs_without_balanced_global_optimum": len(counterexamples),
        "counterexamples": counterexamples,
        "records": records,
    }
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
