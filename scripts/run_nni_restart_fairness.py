"""Budget-matched restart audit for NEST and external SE constructors.

This audit is deliberately separate from the frozen TAMC evidence.  It uses a
new independent HSBM stream and selects every candidate using structural
entropy only; the exact optimum is consulted only after selection.

Candidate-budget protocol (default B=32):

* NEST-RB: the paper's standard deterministic pool plus B random-coalescent
  starts, all NNI-refined.  NEST-coalescent-B reports the random starts alone.
* HCSE-B: B constructor calls, balanced over target heights 2, 3, 4, and 5.
* BBM-oracle-B: B calls with the planted fine-cluster count (an oracle).
* BBM-label-free-B: B calls balanced over a predeclared k grid, with the lowest
  structural entropy selected without labels.

The artifact also reports a post-hoc wall-clock-matched prefix for HCSE and BBM
using NEST-RB's measured runtime on the same graph.  Checkpointing makes the run
safe to resume.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import random
import sys
import time
from pathlib import Path

import networkx as nx
import numpy as np
from scipy import stats

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.run_nni_benchmark import (  # noqa: E402
    load_hcse,
    louvain_two_level,
)
from scripts.run_nni_optimality import (  # noqa: E402
    REGIMES,
    small_hierarchical_sbm,
)
from scripts.run_nni_restart_audit import (  # noqa: E402
    is_optimal,
    relative_gap,
)
from selib.htree import (  # noqa: E402
    _graph_arrays,
    annotate,
    encoding_tree_nni_fast,
    hd_se,
    linkage_to_tree,
)
from selib.optimality import exact_tree_entropy  # noqa: E402
from selib.se import se_agglomerative  # noqa: E402


METHODS = (
    "NEST-R32",
    "NEST-coalescent-B32",
    "HCSE-B32",
    "BBM-oracle-B32",
    "BBM-label-free-B32",
    "SE-agglomerative",
    "Louvain-2L",
)


def proportional_sizes(sizes, target_n):
    """Resize a planted block pattern while preserving its relative imbalance."""
    sizes = list(sizes)
    if target_n < len(sizes):
        raise ValueError("target_n must leave at least one vertex per fine block")
    scale = target_n / sum(sizes)
    resized = [max(1, math.floor(size * scale)) for size in sizes]
    residual_order = sorted(
        range(len(sizes)),
        key=lambda index: (-(sizes[index] * scale - resized[index]), index),
    )
    while sum(resized) < target_n:
        for index in residual_order:
            if sum(resized) >= target_n:
                break
            resized[index] += 1
    while sum(resized) > target_n:
        candidates = [index for index, size in enumerate(resized) if size > 1]
        if not candidates:
            raise ValueError("cannot shrink block pattern to target_n")
        index = min(
            candidates,
            key=lambda item: (sizes[item] * scale - resized[item], item),
        )
        resized[index] -= 1
    return resized


def score_tree(root, deg, adj, volume):
    annotate(root, deg, adj, volume)
    return float(hd_se(root, volume))


def candidate_call(build, deg, adj, volume, seed):
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))
    started = time.perf_counter()
    try:
        root = build()
        elapsed = time.perf_counter() - started
        return {
            "entropy_bits": score_tree(root, deg, adj, volume),
            "time_s": elapsed,
            "seed": seed,
        }
    except Exception as error:
        return {
            "time_s": time.perf_counter() - started,
            "seed": seed,
            "error": repr(error),
        }


def best_record(candidates, optimum):
    successful = [item for item in candidates if "entropy_bits" in item]
    if not successful:
        return {
            "status": "failed",
            "entropy_bits": None,
            "additive_gap_bits": None,
            "relative_gap_percent": None,
            "globally_optimal": False,
            "candidate_calls": len(candidates),
            "successful_candidate_calls": 0,
            "failed_candidate_calls": len(candidates),
            "unique_entropies_1e-10": 0,
            "total_time_s": float(sum(x["time_s"] for x in candidates)),
            "candidates": candidates,
        }
    best = min(successful, key=lambda item: item["entropy_bits"])
    entropy = best["entropy_bits"]
    return {
        "status": "ok",
        "entropy_bits": entropy,
        "additive_gap_bits": max(0.0, entropy - optimum),
        "relative_gap_percent": relative_gap(entropy, optimum),
        "globally_optimal": is_optimal(entropy, optimum),
        "candidate_calls": len(candidates),
        "successful_candidate_calls": len(successful),
        "failed_candidate_calls": len(candidates) - len(successful),
        "unique_entropies_1e-10": len({round(x["entropy_bits"], 10) for x in successful}),
        "total_time_s": float(sum(x["time_s"] for x in candidates)),
        "selected_candidate": best,
        "candidates": candidates,
    }


def time_matched_record(candidates, budget_s, optimum):
    chosen = []
    elapsed = 0.0
    for candidate in candidates:
        if chosen and elapsed + candidate["time_s"] > budget_s:
            break
        chosen.append(candidate)
        elapsed += candidate["time_s"]
    result = best_record(chosen, optimum)
    result["wall_budget_s"] = budget_s
    result["prefix_time_s"] = elapsed
    return result


def deterministic_baselines(graph, deg, adj, volume, graph_seed):
    outputs = {}
    start = time.perf_counter()
    root = linkage_to_tree(se_agglomerative(graph), len(graph))
    outputs["SE-agglomerative"] = {
        "entropy_bits": score_tree(root, deg, adj, volume),
        "candidate_calls": 1,
        "total_time_s": time.perf_counter() - start,
    }
    start = time.perf_counter()
    root = louvain_two_level(graph, graph_seed)
    outputs["Louvain-2L"] = {
        "entropy_bits": score_tree(root, deg, adj, volume),
        "candidate_calls": 1,
        "total_time_s": time.perf_counter() - start,
    }
    return outputs


def evaluate_graph(
    regime,
    graph_seed,
    campaign_seed,
    budget,
    hcse_api,
    sizes_override=None,
    max_nodes=12,
):
    graph, manifest = small_hierarchical_sbm(
        regime,
        graph_seed,
        independent_regime_seed=True,
        sizes_override=sizes_override,
    )
    optimum = exact_tree_entropy(graph, max_nodes=max_nodes)
    _, _, n, adj, deg, volume = _graph_arrays(graph)
    fine_k = len(REGIMES[regime][1])
    regime_index = list(REGIMES).index(regime)
    restart_seed = campaign_seed * 10_000_000 + regime_index * 100_000 + graph_seed

    nest_started = time.perf_counter()
    _, _, _, _, nest_audit = encoding_tree_nni_fast(
        graph,
        seed=graph_seed,
        random_restarts=budget,
        restart_seed=restart_seed,
        return_trace=True,
    )
    nest_time = time.perf_counter() - nest_started
    nest_entropy = float(nest_audit["selected_entropy"])
    random_entropies = [
        float(value)
        for name, value in nest_audit["candidate_entropies"].items()
        if name.startswith("random-coalescent-")
    ]
    if len(random_entropies) != budget:
        raise RuntimeError(f"expected {budget} random NEST starts, got {len(random_entropies)}")

    outcomes = {
        f"NEST-R{budget}": {
            "entropy_bits": nest_entropy,
            "additive_gap_bits": max(0.0, nest_entropy - optimum),
            "relative_gap_percent": relative_gap(nest_entropy, optimum),
            "globally_optimal": is_optimal(nest_entropy, optimum),
            "candidate_calls": len(nest_audit["candidate_entropies"]),
            "random_restarts": budget,
            "total_time_s": nest_time,
            "selected_initializer": nest_audit["selected_initializer"],
            "candidate_entropies": nest_audit["candidate_entropies"],
        },
        f"NEST-coalescent-B{budget}": {
            "entropy_bits": min(random_entropies),
            "additive_gap_bits": max(0.0, min(random_entropies) - optimum),
            "relative_gap_percent": relative_gap(min(random_entropies), optimum),
            "globally_optimal": is_optimal(min(random_entropies), optimum),
            "candidate_calls": budget,
            "unique_entropies_1e-10": len({round(x, 10) for x in random_entropies}),
            "total_time_s": nest_time,
            "timing_note": "shared run with NEST-RB; includes standard-pool overhead",
            "candidate_entropies": random_entropies,
        },
    }

    hcse, bbm = hcse_api
    seed_base = restart_seed + 1_000_000_000
    heights = (2, 3, 4, 5)
    hcse_candidates = []
    for index in range(budget):
        height = heights[index % len(heights)]
        candidate = candidate_call(
            lambda height=height: hcse(graph, height),
            deg,
            adj,
            volume,
            seed_base + index,
        )
        candidate["target_height"] = height
        hcse_candidates.append(candidate)

    oracle_candidates = []
    for index in range(budget):
        candidate = candidate_call(
            lambda: bbm(graph, fine_k),
            deg,
            adj,
            volume,
            seed_base + 100_000 + index,
        )
        candidate["k"] = fine_k
        oracle_candidates.append(candidate)

    k_grid = list(range(2, min(8, n - 1) + 1))
    label_free_candidates = []
    for index in range(budget):
        k = k_grid[index % len(k_grid)]
        candidate = candidate_call(
            lambda k=k: bbm(graph, k),
            deg,
            adj,
            volume,
            seed_base + 200_000 + index,
        )
        candidate["k"] = k
        label_free_candidates.append(candidate)

    outcomes[f"HCSE-B{budget}"] = best_record(hcse_candidates, optimum)
    outcomes[f"BBM-oracle-B{budget}"] = best_record(oracle_candidates, optimum)
    outcomes[f"BBM-label-free-B{budget}"] = best_record(label_free_candidates, optimum)
    outcomes[f"HCSE-time-matched-to-NEST-R{budget}"] = time_matched_record(
        hcse_candidates, nest_time, optimum
    )
    outcomes[f"BBM-oracle-time-matched-to-NEST-R{budget}"] = time_matched_record(
        oracle_candidates, nest_time, optimum
    )
    outcomes[f"BBM-label-free-time-matched-to-NEST-R{budget}"] = time_matched_record(
        label_free_candidates, nest_time, optimum
    )

    for name, outcome in deterministic_baselines(
        graph, deg, adj, volume, graph_seed
    ).items():
        entropy = outcome["entropy_bits"]
        outcome.update({
            "additive_gap_bits": max(0.0, entropy - optimum),
            "relative_gap_percent": relative_gap(entropy, optimum),
            "globally_optimal": is_optimal(entropy, optimum),
        })
        outcomes[name] = outcome

    return {
        "regime": regime,
        "graph_seed": graph_seed,
        "manifest": manifest,
        "n": n,
        "m": graph.number_of_edges(),
        "global_optimum_bits": optimum,
        "restart_rng_seed": restart_seed,
        "outcomes": outcomes,
    }


def mean_ci(values):
    values = np.asarray(values, dtype=float)
    mean = float(np.mean(values))
    if len(values) < 2:
        return {"mean": mean, "ci95": 0.0}
    return {
        "mean": mean,
        "ci95": float(stats.t.ppf(0.975, len(values) - 1) * stats.sem(values)),
    }


def summarize(records):
    methods = sorted({name for row in records for name in row["outcomes"]})
    summary = {}
    for method in methods:
        outcomes = [row["outcomes"][method] for row in records]
        successful = [
            x for x in outcomes
            if x.get("status", "ok") == "ok"
            and math.isfinite(x["relative_gap_percent"])
        ]
        gaps = [x["relative_gap_percent"] for x in successful]
        times = [x["total_time_s"] for x in outcomes]
        summary[method] = {
            "instances": len(outcomes),
            "successful_instances": len(successful),
            "failed_instances": len(outcomes) - len(successful),
            "globally_optimal": sum(x["globally_optimal"] for x in outcomes),
            "optimal_hit_rate_percent": 100.0 * sum(
                x["globally_optimal"] for x in outcomes
            ) / len(outcomes),
            "mean_relative_gap_percent": mean_ci(gaps) if gaps else None,
            "max_relative_gap_percent": float(max(gaps)) if gaps else None,
            "mean_total_time_s": mean_ci(times),
            "mean_candidate_calls": float(np.mean([
                x["candidate_calls"] for x in outcomes
            ])),
        }
    return summary


def write_artifact(path, protocol, records, started):
    artifact = {
        "protocol": protocol,
        "environment": {
            "python": platform.python_version(),
            "networkx": nx.__version__,
            "numpy": np.__version__,
        },
        "records": records,
        "summary": summarize(records) if records else {},
        "summary_by_regime": {
            regime: summarize([row for row in records if row["regime"] == regime])
            for regime in REGIMES
            if any(row["regime"] == regime for row in records)
        },
        "elapsed_s": time.perf_counter() - started,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/nni_restart_fairness.json")
    parser.add_argument("--hcse-dir", default="external/HCSE")
    parser.add_argument("--seed-start", type=int, default=160)
    parser.add_argument("--seeds", type=int, default=50)
    parser.add_argument("--budget", type=int, default=32)
    parser.add_argument("--campaign-seed", type=int, default=20260810)
    parser.add_argument(
        "--sizes",
        help="comma-separated fine-block sizes; defaults to each regime's n=12 design",
    )
    parser.add_argument(
        "--target-n",
        type=int,
        help="proportionally resize each regime's native block pattern to this n",
    )
    parser.add_argument("--max-nodes", type=int, default=12)
    parser.add_argument("--max-graphs", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.budget < 4 or args.budget % 4:
        raise ValueError("budget must be a positive multiple of four")
    sizes_override = None
    if args.sizes and args.target_n:
        raise ValueError("use only one of --sizes and --target-n")
    if args.sizes:
        sizes_override = [int(value) for value in args.sizes.split(",")]
        if len(sizes_override) % 2 or any(value <= 0 for value in sizes_override):
            raise ValueError("--sizes must contain a positive, even-length list")
        if sum(sizes_override) > args.max_nodes:
            raise ValueError("sum(--sizes) exceeds --max-nodes")
    if args.target_n and args.target_n > args.max_nodes:
        raise ValueError("--target-n exceeds --max-nodes")
    sizes_by_regime = {
        regime: (
            proportional_sizes(REGIMES[regime][1], args.target_n)
            if args.target_n
            else sizes_override
        )
        for regime in REGIMES
    }

    output = Path(args.output)
    protocol = json.loads(json.dumps({
        "version": "tamc-nest-restart-fairness-v1",
        "purpose": "new sealed compute- and candidate-budget fairness audit",
        "graph_seeds": [args.seed_start, args.seed_start + args.seeds - 1],
        "independent_regime_seeds": True,
        "candidate_budget": args.budget,
        "sizes_override": sizes_override,
        "target_n": args.target_n,
        "sizes_by_regime": sizes_by_regime,
        "n": args.target_n or (sum(sizes_override) if sizes_override else 12),
        "exact_max_nodes": args.max_nodes,
        "frozen_selected_budget": args.budget,
        "selection": "minimum structural entropy; exact optimum unseen by every method",
        "hcse_schedule": "equal calls at target heights 2,3,4,5",
        "bbm_oracle": "planted fine-k; explicitly favorable to BBM",
        "bbm_label_free_k_grid": list(range(2, 9)),
        "time_matching": "best completed candidate prefix within measured NEST-RB wall time",
        "regimes": REGIMES,
        "campaign_seed": args.campaign_seed,
    }))
    records = []
    if args.resume and output.exists():
        previous = json.loads(output.read_text())
        if previous["protocol"] != protocol:
            raise ValueError("existing artifact protocol differs; refuse unsafe resume")
        records = previous["records"]
    done = {(row["regime"], row["graph_seed"]) for row in records}

    hcse_api = load_hcse(args.hcse_dir)
    started = time.perf_counter()
    completed_this_run = 0
    for regime in REGIMES:
        for graph_seed in range(args.seed_start, args.seed_start + args.seeds):
            key = (regime, graph_seed)
            if key in done:
                continue
            row = evaluate_graph(
                regime,
                graph_seed,
                args.campaign_seed,
                args.budget,
                hcse_api,
                sizes_override=sizes_by_regime[regime],
                max_nodes=args.max_nodes,
            )
            records.append(row)
            completed_this_run += 1
            write_artifact(output, protocol, records, started)
            compact = {
                name: (
                    outcome["globally_optimal"],
                    (
                        round(outcome["relative_gap_percent"], 4)
                        if outcome["relative_gap_percent"] is not None
                        else None
                    ),
                    round(outcome["total_time_s"], 3),
                )
                for name, outcome in row["outcomes"].items()
                if name in {
                    f"NEST-R{args.budget}",
                    f"HCSE-B{args.budget}",
                    f"BBM-oracle-B{args.budget}",
                    f"BBM-label-free-B{args.budget}",
                }
            }
            print(f"[{regime} seed={graph_seed}] {compact}", flush=True)
            if args.max_graphs and completed_this_run >= args.max_graphs:
                print(json.dumps(summarize(records), indent=2))
                return
    print(json.dumps(summarize(records), indent=2))


if __name__ == "__main__":
    main()
