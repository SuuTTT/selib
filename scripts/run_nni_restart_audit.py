"""Audit randomized restart repair for NEST against exact small-graph optima.

The original 50 instances (seeds 0--9) are treated as development data.  A
configurable disjoint seed range can then serve as holdout or confirmation
data. Random starts never inspect the exact optimum; the dynamic program is
used only for after-the-fact evaluation.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import sys
import time
from pathlib import Path

import networkx as nx
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.run_nni_optimality import REGIMES, small_hierarchical_sbm
from selib.htree import (
    _graph_arrays,
    annotate,
    encoding_tree_nni_fast,
    hd_se,
    random_coalescent_tree,
    refine_nni,
    refine_nni_compound,
)
from selib.optimality import exact_tree_entropy


RESTART_BUDGETS = (4, 8, 16, 32)
OPTIMALITY_ATOL = 1e-9
OPTIMALITY_RTOL = 1e-8


def is_optimal(observed: float, optimum: float) -> bool:
    tolerance = max(OPTIMALITY_ATOL, OPTIMALITY_RTOL * abs(optimum))
    return observed - optimum <= tolerance


def relative_gap(observed: float, optimum: float) -> float:
    gap = max(0.0, observed - optimum)
    return 100.0 * gap / optimum if optimum > 0 else 0.0


def summarize(records, key):
    gaps = [row[key]["relative_gap_percent"] for row in records]
    return {
        "instances": len(records),
        "globally_optimal": sum(row[key]["globally_optimal"] for row in records),
        "optimal_hit_rate_percent": 100.0 * sum(
            row[key]["globally_optimal"] for row in records
        ) / len(records),
        "mean_relative_gap_percent": float(np.mean(gaps)),
        "median_relative_gap_percent": float(np.median(gaps)),
        "max_relative_gap_percent": float(np.max(gaps)),
    }


def evaluate_split(
    split, seed_start, seed_stop, campaign_seed, independent_regime_seed=False
):
    records = []
    started = time.perf_counter()
    for regime_index, regime in enumerate(REGIMES):
        for graph_seed in range(seed_start, seed_stop):
            graph, manifest = small_hierarchical_sbm(
                regime,
                graph_seed,
                independent_regime_seed=independent_regime_seed,
            )
            optimum = exact_tree_entropy(graph, max_nodes=12)

            base_root, _, _, volume = encoding_tree_nni_fast(
                graph, seed=graph_seed
            )
            base_entropy = hd_se(base_root, volume)
            observed = {0: base_entropy}

            _, _, n, adj, deg, volume = _graph_arrays(graph)
            rng_seed = (
                campaign_seed * 10_000_000
                + regime_index * 100_000
                + graph_seed
            )
            rng = random.Random(rng_seed)
            best = base_entropy
            for restart in range(1, max(RESTART_BUDGETS) + 1):
                root = random_coalescent_tree(n, rng)
                annotate(root, deg, adj, volume)
                root = refine_nni(root, deg, adj, volume)
                root = refine_nni_compound(root, deg, adj, volume)
                annotate(root, deg, adj, volume)
                best = min(best, hd_se(root, volume))
                if restart in RESTART_BUDGETS:
                    observed[restart] = best

            row = {
                "split": split,
                "regime": regime,
                "graph_seed": graph_seed,
                "n": len(graph),
                "m": graph.number_of_edges(),
                "manifest": manifest,
                "global_optimum_bits": optimum,
                "restart_rng_seed": rng_seed,
            }
            for budget, entropy in observed.items():
                label = "baseline" if budget == 0 else f"restart_{budget}"
                row[label] = {
                    "entropy_bits": entropy,
                    "additive_gap_bits": max(0.0, entropy - optimum),
                    "relative_gap_percent": relative_gap(entropy, optimum),
                    "globally_optimal": is_optimal(entropy, optimum),
                }
            records.append(row)
            print(
                f"{split:7s} {regime:14s} seed={graph_seed:02d} "
                f"base={row['baseline']['relative_gap_percent']:.3f}% "
                f"R16={row['restart_16']['relative_gap_percent']:.3f}%",
                flush=True,
            )
    labels = ["baseline", *(f"restart_{value}" for value in RESTART_BUDGETS)]
    return {
        "records": records,
        "summary": {label: summarize(records, label) for label in labels},
        "elapsed_s": time.perf_counter() - started,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/nni_restart_audit.json")
    parser.add_argument("--campaign-seed", type=int, default=20260810)
    parser.add_argument("--skip-development", action="store_true")
    parser.add_argument("--holdout-start", type=int, default=10)
    parser.add_argument("--holdout-seeds", type=int, default=50)
    parser.add_argument("--independent-regime-seeds", action="store_true")
    args = parser.parse_args()

    artifact = {
        "protocol": {
            "version": "tamc-nest-restart-audit-v1",
            "development_graph_seeds": [0, 9],
            "holdout_graph_seeds": [
                args.holdout_start,
                args.holdout_start + args.holdout_seeds - 1,
            ],
            "restart_budgets": list(RESTART_BUDGETS),
            "frozen_selected_budget": 16,
            "start_distribution": "random pairwise coalescent; not uniform over topologies",
            "selection": "lowest structural entropy; exact optimum unseen by optimizer",
            "optimality_tolerance": {
                "absolute": OPTIMALITY_ATOL,
                "relative": OPTIMALITY_RTOL,
            },
            "campaign_seed": args.campaign_seed,
            "independent_regime_seeds": args.independent_regime_seeds,
            "regimes": REGIMES,
        },
        "environment": {
            "python": platform.python_version(),
            "networkx": nx.__version__,
            "numpy": np.__version__,
        },
    }
    if not args.skip_development:
        artifact["development"] = evaluate_split(
            "develop", 0, 10, args.campaign_seed,
            independent_regime_seed=args.independent_regime_seeds,
        )
    artifact["holdout"] = evaluate_split(
        "holdout",
        args.holdout_start,
        args.holdout_start + args.holdout_seeds,
        args.campaign_seed,
        independent_regime_seed=args.independent_regime_seeds,
    )

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps({
        split: value["summary"]
        for split, value in artifact.items()
        if split in {"development", "holdout"}
    }, indent=2))


if __name__ == "__main__":
    main()
