"""Measure NEST random-start basins exactly at n<=8 and by Monte Carlo at n=12.

The optimizer never receives the exact optimum or planted blocks.  Those are
used only after each endpoint has been independently produced and rescored.
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
from scipy.stats import beta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.run_nni_optimality import REGIMES, small_hierarchical_sbm
from scripts.run_nni_restart_audit import is_optimal
from selib.basin import (
    coalescent_history_count,
    coalescent_history_total,
    planted_recovery,
    rooted_binary_topologies,
    topology_to_tree,
)
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


EXACT_SIZES = {
    5: [1, 1, 1, 2],
    6: [1, 2, 1, 2],
    7: [1, 2, 2, 2],
    8: [2, 2, 2, 2],
}
IMBALANCED_EXACT_SIZES = {
    5: [1, 1, 1, 2],
    6: [1, 2, 1, 2],
    7: [1, 2, 1, 3],
    8: [1, 3, 1, 3],
}
HARD_N12_CASES = (
    ("noisy", 0),
    ("noisy", 8),
    ("noisy", 9),
    ("imbalanced", 0),
    ("weak-hierarchy", 9),
    ("noisy", 11),
    ("noisy", 17),
    ("weak-hierarchy", 17),
)


def refine_start(root, deg, adj, volume):
    annotate(root, deg, adj, volume)
    root = refine_nni(root, deg, adj, volume)
    root = refine_nni_compound(root, deg, adj, volume)
    annotate(root, deg, adj, volume)
    return root, hd_se(root, volume)


def events(root, entropy, optimum, manifest):
    recovered = planted_recovery(
        root, manifest["fine_blocks"], manifest["coarse_blocks"]
    )
    optimal = is_optimal(entropy, optimum)
    return {
        "optimal": optimal,
        "strict_recovery": recovered["strict_recovered"],
        "both": optimal and recovered["strict_recovered"],
    }


def probability_record(successes, trials, confidence=0.95):
    estimate = successes / trials
    alpha = 1.0 - confidence
    lower = 0.0 if successes == 0 else float(
        beta.ppf(alpha / 2.0, successes, trials - successes + 1)
    )
    upper = 1.0 if successes == trials else float(
        beta.ppf(1.0 - alpha / 2.0, successes + 1, trials - successes)
    )
    return {
        "successes": successes,
        "trials": trials,
        "estimate": estimate,
        "clopper_pearson_95ci": [lower, upper],
    }


def restart_success_probability(per_start_probability, restarts):
    return 1.0 - (1.0 - per_start_probability) ** restarts


def standard_pool_result(graph, graph_seed, optimum):
    root, _, _, volume = encoding_tree_nni_fast(graph, seed=graph_seed)
    entropy = hd_se(root, volume)
    return {
        "entropy_bits": entropy,
        "globally_optimal": is_optimal(entropy, optimum),
    }


def exact_audit(regimes, min_n, max_n, graph_seed):
    records = []
    started = time.perf_counter()
    for n in range(min_n, max_n + 1):
        topologies = rooted_binary_topologies(n)
        history_weights = [
            coalescent_history_count(topology) for topology in topologies
        ]
        history_total = coalescent_history_total(n)
        if sum(history_weights) != history_total:
            raise AssertionError("enumerated topology mass does not sum to one")

        for regime in regimes:
            sizes = (
                IMBALANCED_EXACT_SIZES[n]
                if regime == "imbalanced" else EXACT_SIZES[n]
            )
            graph, manifest = small_hierarchical_sbm(
                regime,
                graph_seed + n,
                independent_regime_seed=True,
                sizes_override=sizes,
            )
            optimum = exact_tree_entropy(graph, max_nodes=8)
            _, _, _, adj, deg, volume = _graph_arrays(graph)
            counts = {"optimal": 0, "strict_recovery": 0, "both": 0}
            weighted = {"optimal": 0, "strict_recovery": 0, "both": 0}
            gaps = []
            graph_started = time.perf_counter()
            for index, (topology, weight) in enumerate(
                zip(topologies, history_weights), start=1
            ):
                root, entropy = refine_start(
                    topology_to_tree(topology), deg, adj, volume
                )
                observed = events(root, entropy, optimum, manifest)
                gaps.append(max(0.0, entropy - optimum))
                for key, hit in observed.items():
                    counts[key] += int(hit)
                    weighted[key] += weight * int(hit)
                if index % 25000 == 0:
                    print(
                        f"exact n={n} {regime}: {index}/{len(topologies)}",
                        flush=True,
                    )

            baseline = standard_pool_result(graph, graph_seed + n, optimum)
            uniform = {
                key: {
                    "successes": counts[key],
                    "topologies": len(topologies),
                    "probability": counts[key] / len(topologies),
                }
                for key in counts
            }
            coalescent = {
                key: {
                    "successful_histories": weighted[key],
                    "total_histories": history_total,
                    "probability": weighted[key] / history_total,
                }
                for key in weighted
            }
            p = coalescent["optimal"]["probability"]
            record = {
                "regime": regime,
                "n": n,
                "m": graph.number_of_edges(),
                "manifest": manifest,
                "global_optimum_bits": optimum,
                "standard_pool": baseline,
                "uniform_topology_measure": uniform,
                "coalescent_measure": coalescent,
                "strict_given_optimal": (
                    counts["both"] / counts["optimal"]
                    if counts["optimal"] else None
                ),
                "coalescent_strict_given_optimal": (
                    weighted["both"] / weighted["optimal"]
                    if weighted["optimal"] else None
                ),
                "predicted_nest_r32_optimal_probability": (
                    1.0 if baseline["globally_optimal"]
                    else restart_success_probability(p, 32)
                ),
                "endpoint_additive_gap_bits": {
                    "mean": float(np.mean(gaps)),
                    "median": float(np.median(gaps)),
                    "maximum": float(np.max(gaps)),
                },
                "elapsed_s": time.perf_counter() - graph_started,
            }
            records.append(record)
            print(
                f"exact n={n} {regime}: p_opt={p:.6f}, "
                f"p_truth={coalescent['strict_recovery']['probability']:.6f}",
                flush=True,
            )

    return {
        "protocol": {
            "version": "tamc-nest-basin-exact-v1",
            "measure": "all unordered rooted binary labeled topologies, reported both uniformly and under the pairwise-coalescent history measure",
            "sizes": {
                str(n): EXACT_SIZES[n] for n in range(min_n, max_n + 1)
            },
            "imbalanced_sizes": {
                str(n): IMBALANCED_EXACT_SIZES[n]
                for n in range(min_n, max_n + 1)
            },
            "graph_seed_base": graph_seed,
            "regimes": list(regimes),
            "optimizer": "one-step NNI descent followed by bounded two-step compound search",
            "evaluation_only": "H* and planted blocks are never visible to the optimizer",
            "strict_recovery": "every declared fine and coarse block occurs as a descendant-leaf clade; singleton fine blocks are trivially recovered",
        },
        "records": records,
        "elapsed_s": time.perf_counter() - started,
    }


def monte_carlo_audit(cases, starts, campaign_seed):
    records = []
    started = time.perf_counter()
    for case_index, (regime, graph_seed) in enumerate(cases):
        graph, manifest = small_hierarchical_sbm(regime, graph_seed)
        optimum = exact_tree_entropy(graph, max_nodes=12)
        baseline = standard_pool_result(graph, graph_seed, optimum)
        _, _, n, adj, deg, volume = _graph_arrays(graph)
        rng_seed = campaign_seed + case_index * 1_000_003
        rng = random.Random(rng_seed)
        counts = {"optimal": 0, "strict_recovery": 0, "both": 0}
        gaps = []
        graph_started = time.perf_counter()
        for start in range(1, starts + 1):
            root, entropy = refine_start(
                random_coalescent_tree(n, rng), deg, adj, volume
            )
            observed = events(root, entropy, optimum, manifest)
            gaps.append(max(0.0, entropy - optimum))
            for key, hit in observed.items():
                counts[key] += int(hit)
            if start % 1000 == 0:
                print(
                    f"MC {regime} seed={graph_seed}: {start}/{starts}",
                    flush=True,
                )

        probabilities = {
            key: probability_record(value, starts)
            for key, value in counts.items()
        }
        p = probabilities["optimal"]
        p["predicted_random_r32"] = restart_success_probability(
            p["estimate"], 32
        )
        p["predicted_random_r32_from_95ci"] = [
            restart_success_probability(p["clopper_pearson_95ci"][0], 32),
            restart_success_probability(p["clopper_pearson_95ci"][1], 32),
        ]
        record = {
            "regime": regime,
            "graph_seed": graph_seed,
            "n": n,
            "m": graph.number_of_edges(),
            "manifest": manifest,
            "restart_rng_seed": rng_seed,
            "global_optimum_bits": optimum,
            "standard_pool": baseline,
            "probabilities": probabilities,
            "strict_given_optimal": (
                counts["both"] / counts["optimal"]
                if counts["optimal"] else None
            ),
            "endpoint_additive_gap_bits": {
                "mean": float(np.mean(gaps)),
                "median": float(np.median(gaps)),
                "p95": float(np.quantile(gaps, 0.95)),
                "maximum": float(np.max(gaps)),
            },
            "elapsed_s": time.perf_counter() - graph_started,
        }
        records.append(record)
        print(
            f"MC {regime} seed={graph_seed}: "
            f"p_opt={p['estimate']:.6f}, "
            f"p_truth={probabilities['strict_recovery']['estimate']:.6f}",
            flush=True,
        )

    return {
        "protocol": {
            "version": "tamc-nest-basin-monte-carlo-v1",
            "cases": [list(case) for case in cases],
            "starts_per_graph": starts,
            "campaign_seed": campaign_seed,
            "start_distribution": "independent pairwise coalescent starts",
            "interval": "two-sided exact Clopper-Pearson 95% interval",
            "optimizer": "one-step NNI descent followed by bounded two-step compound search",
            "evaluation_only": "H* and planted blocks are never visible to the optimizer",
            "strict_recovery": "every declared fine and coarse block occurs as a descendant-leaf clade",
        },
        "environment": {
            "python": platform.python_version(),
            "networkx": nx.__version__,
            "numpy": np.__version__,
        },
        "records": records,
        "elapsed_s": time.perf_counter() - started,
    }


def write_json(path, artifact):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("exact", "monte-carlo", "both"), default="both"
    )
    parser.add_argument("--exact-output", default="results/nni_basin_exact.json")
    parser.add_argument(
        "--monte-carlo-output", default="results/nni_basin_monte_carlo.json"
    )
    parser.add_argument("--exact-min-n", type=int, default=5)
    parser.add_argument("--exact-max-n", type=int, default=8)
    parser.add_argument("--exact-graph-seed", type=int, default=20260810)
    parser.add_argument("--exact-regimes", nargs="+", choices=REGIMES, default=list(REGIMES))
    parser.add_argument("--starts", type=int, default=10000)
    parser.add_argument("--campaign-seed", type=int, default=20260810)
    args = parser.parse_args()

    if not 5 <= args.exact_min_n <= args.exact_max_n <= 8:
        parser.error("exact range must satisfy 5 <= min <= max <= 8")
    if args.starts <= 0:
        parser.error("--starts must be positive")

    if args.mode in {"exact", "both"}:
        write_json(
            args.exact_output,
            exact_audit(
                args.exact_regimes,
                args.exact_min_n,
                args.exact_max_n,
                args.exact_graph_seed,
            ),
        )
    if args.mode in {"monte-carlo", "both"}:
        write_json(
            args.monte_carlo_output,
            monte_carlo_audit(HARD_N12_CASES, args.starts, args.campaign_seed),
        )


if __name__ == "__main__":
    main()
