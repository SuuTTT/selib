"""Measure stochastic optimal-hit rates on hard exact-audit instances."""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.run_nni_optimality import REGIMES, small_hierarchical_sbm
from scripts.run_nni_restart_audit import (
    is_optimal,
    random_coalescent_tree,
    relative_gap,
)
from selib.htree import (
    _graph_arrays,
    annotate,
    encoding_tree_nni_fast,
    hd_se,
    refine_nni,
    refine_nni_compound,
)
from selib.optimality import exact_tree_entropy


CASES = (("noisy", 11), ("noisy", 17), ("weak-hierarchy", 17))
BUDGETS = (16, 32, 64, 128)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaigns", type=int, default=20)
    parser.add_argument(
        "--output", default="results/nni_restart_failure_diagnostics.json"
    )
    args = parser.parse_args()

    records = []
    started = time.perf_counter()
    for regime, graph_seed in CASES:
        graph, manifest = small_hierarchical_sbm(regime, graph_seed)
        optimum = exact_tree_entropy(graph, max_nodes=12)
        baseline_root, _, _, baseline_volume = encoding_tree_nni_fast(
            graph, seed=graph_seed
        )
        baseline_entropy = hd_se(baseline_root, baseline_volume)
        _, _, n, adj, deg, volume = _graph_arrays(graph)
        regime_index = list(REGIMES).index(regime)

        for campaign in range(args.campaigns):
            rng_seed = (
                91_000_000
                + campaign * 1_000_000
                + regime_index * 10_000
                + graph_seed
            )
            rng = random.Random(rng_seed)
            best = baseline_entropy
            outcomes = {}
            first_hit = None
            for restart in range(1, max(BUDGETS) + 1):
                root = random_coalescent_tree(n, rng)
                annotate(root, deg, adj, volume)
                root = refine_nni(root, deg, adj, volume)
                root = refine_nni_compound(root, deg, adj, volume)
                annotate(root, deg, adj, volume)
                best = min(best, hd_se(root, volume))
                if first_hit is None and is_optimal(best, optimum):
                    first_hit = restart
                if restart in BUDGETS:
                    outcomes[str(restart)] = {
                        "globally_optimal": is_optimal(best, optimum),
                        "relative_gap_percent": relative_gap(best, optimum),
                    }
            records.append({
                "regime": regime,
                "graph_seed": graph_seed,
                "campaign": campaign,
                "restart_rng_seed": rng_seed,
                "global_optimum_bits": optimum,
                "baseline_relative_gap_percent": relative_gap(
                    baseline_entropy, optimum
                ),
                "first_hit_restart": first_hit,
                "outcomes": outcomes,
                "manifest": manifest,
            })
            print(
                f"{regime:14s} graph={graph_seed:02d} campaign={campaign:02d} "
                f"first_hit={first_hit}",
                flush=True,
            )

    summary = {}
    for regime, graph_seed in CASES:
        rows = [
            row for row in records
            if row["regime"] == regime and row["graph_seed"] == graph_seed
        ]
        key = f"{regime}/seed-{graph_seed}"
        summary[key] = {
            "campaigns": len(rows),
            "baseline_relative_gap_percent": rows[0][
                "baseline_relative_gap_percent"
            ],
            "budgets": {},
        }
        for budget in BUDGETS:
            budget_rows = [row["outcomes"][str(budget)] for row in rows]
            gaps = [row["relative_gap_percent"] for row in budget_rows]
            hits = sum(row["globally_optimal"] for row in budget_rows)
            summary[key]["budgets"][str(budget)] = {
                "optimal_hits": hits,
                "optimal_hit_rate_percent": 100.0 * hits / len(rows),
                "mean_relative_gap_percent": float(np.mean(gaps)),
                "max_relative_gap_percent": float(np.max(gaps)),
            }

    artifact = {
        "protocol": {
            "version": "tamc-nest-hard-case-restart-v1",
            "cases": [list(case) for case in CASES],
            "campaigns": args.campaigns,
            "restart_budgets": list(BUDGETS),
            "selection": "lowest structural entropy; exact optimum unseen by optimizer",
        },
        "summary": summary,
        "records": records,
        "elapsed_s": time.perf_counter() - started,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
