#!/usr/bin/env python3
"""Run the frozen, disjoint NEST-G confirmatory exact audit.

The protocol is read from JSON and checked before any graph is evaluated.
For each graph, all candidate trees are selected using structural entropy
alone.  The exact dynamic-programming optimum is computed only after the
rotation-only and graft-refined endpoints have been selected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import statistics
import sys
import time
from pathlib import Path

import networkx as nx
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_nni_optimality import REGIMES, small_hierarchical_sbm
from selib.htree import (
    _graph_arrays,
    annotate,
    hd_se,
    random_coalescent_tree,
    refine_graft,
    refine_nni,
    refine_nni_compound,
)
from selib.optimality import exact_tree_entropy


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_hit(value: float, optimum: float, atol: float, rtol: float) -> bool:
    return value - optimum <= max(atol, rtol * abs(optimum))


def mean_ci(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    mean = float(np.mean(array))
    if len(array) < 2:
        return {"mean": mean, "ci95_low": mean, "ci95_high": mean}
    half = float(1.959963984540054 * np.std(array, ddof=1) /
                 math.sqrt(len(array)))
    return {"mean": mean, "ci95_low": mean - half, "ci95_high": mean + half}


def binomial_ci(successes: int, total: int) -> dict[str, float]:
    proportion = successes / total
    z = statistics.NormalDist().inv_cdf(0.975)
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    half = (
        z * math.sqrt(
            proportion * (1.0 - proportion) / total
            + z * z / (4.0 * total * total)
        ) / denominator
    )
    low = max(0.0, center - half)
    high = min(1.0, center + half)
    return {"successes": successes, "total": total, "ci95_low": low, "ci95_high": high}


def source_manifest(protocol: dict) -> dict[str, str]:
    return {
        relative: sha256(REPO_ROOT / relative)
        for relative in protocol["frozen_source_sha256"]
    }


def verify_protocol(protocol: dict) -> None:
    expected = protocol["frozen_source_sha256"]
    observed = source_manifest(protocol)
    if observed != expected:
        differences = {
            key: {"expected": expected.get(key), "observed": observed.get(key)}
            for key in sorted(set(expected) | set(observed))
            if expected.get(key) != observed.get(key)
        }
        raise RuntimeError(f"frozen source hash mismatch: {differences}")


def evaluate_graph(regime: str, graph_seed: int, protocol: dict) -> dict:
    graph, manifest = small_hierarchical_sbm(
        regime,
        graph_seed,
        independent_regime_seed=True,
    )
    _, _, n, adjacency, degrees, volume = _graph_arrays(graph)
    regime_index = list(REGIMES).index(regime)
    rng_seed = (
        protocol["campaign_seed"] * 10_000_000
        + regime_index * 100_000
        + graph_seed
    )
    rng = random.Random(rng_seed)
    restarts = []
    graph_started = time.perf_counter()

    for restart in range(protocol["restart_budget"]):
        start = random_coalescent_tree(n, rng)
        annotate(start, degrees, adjacency, volume)

        baseline_started = time.perf_counter()
        baseline = refine_nni(start, degrees, adjacency, volume)
        baseline = refine_nni_compound(
            baseline,
            degrees,
            adjacency,
            volume,
            max_rounds=protocol["compound"]["max_rounds"],
            beam_width=protocol["compound"]["beam_width"],
            barrier_bits=protocol["compound"]["barrier_bits"],
        )
        annotate(baseline, degrees, adjacency, volume)
        baseline_bits = hd_se(baseline, volume)
        baseline_s = time.perf_counter() - baseline_started

        graft_started = time.perf_counter()
        grafted, trace = refine_graft(
            baseline,
            degrees,
            adjacency,
            volume,
            max_rounds=protocol["graft"]["max_rounds"],
            post_nni=True,
            return_trace=True,
        )
        annotate(grafted, degrees, adjacency, volume)
        graft_bits = hd_se(grafted, volume)
        graft_s = time.perf_counter() - graft_started
        graft_steps = [step for step in trace if step["kind"] == "graft"]
        restarts.append({
            "restart": restart,
            "baseline_bits": baseline_bits,
            "graft_bits": graft_bits,
            "improvement_bits": baseline_bits - graft_bits,
            "baseline_s": baseline_s,
            "graft_s": graft_s,
            "accepted_grafts": len(graft_steps),
            "graft_candidates_evaluated": sum(step["candidates"] for step in graft_steps),
        })

    best_baseline = min(item["baseline_bits"] for item in restarts)
    best_graft = min(item["graft_bits"] for item in restarts)

    exact_started = time.perf_counter()
    optimum = exact_tree_entropy(graph, max_nodes=protocol["n"])
    exact_s = time.perf_counter() - exact_started
    atol = protocol["optimality_tolerance"]["absolute"]
    rtol = protocol["optimality_tolerance"]["relative"]
    return {
        "regime": regime,
        "graph_seed": graph_seed,
        "restart_rng_seed": rng_seed,
        "n": n,
        "m": graph.number_of_edges(),
        "manifest": manifest,
        "best_baseline_bits": best_baseline,
        "best_graft_bits": best_graft,
        "paired_improvement_bits": best_baseline - best_graft,
        "exact_optimum_bits": optimum,
        "baseline_gap_bits": max(0.0, best_baseline - optimum),
        "graft_gap_bits": max(0.0, best_graft - optimum),
        "baseline_exact": exact_hit(best_baseline, optimum, atol, rtol),
        "graft_exact": exact_hit(best_graft, optimum, atol, rtol),
        "restarts_improved_by_graft": sum(
            item["improvement_bits"] > atol for item in restarts
        ),
        "baseline_runtime_s": sum(item["baseline_s"] for item in restarts),
        "graft_runtime_s": sum(item["graft_s"] for item in restarts),
        "exact_runtime_s": exact_s,
        "elapsed_s": time.perf_counter() - graph_started,
        "restarts": restarts,
    }


def summarize(records: list[dict]) -> dict:
    baseline_hits = sum(item["baseline_exact"] for item in records)
    graft_hits = sum(item["graft_exact"] for item in records)
    improvements = [item["paired_improvement_bits"] for item in records]
    return {
        "graphs": len(records),
        "baseline_exact": binomial_ci(baseline_hits, len(records)),
        "graft_exact": binomial_ci(graft_hits, len(records)),
        "graphs_strictly_improved": sum(value > 1e-9 for value in improvements),
        "paired_improvement_bits": mean_ci(improvements),
        "baseline_gap_bits": mean_ci([item["baseline_gap_bits"] for item in records]),
        "graft_gap_bits": mean_ci([item["graft_gap_bits"] for item in records]),
        "baseline_runtime_s": mean_ci([item["baseline_runtime_s"] for item in records]),
        "graft_increment_runtime_s": mean_ci([item["graft_runtime_s"] for item in records]),
    }


def write_artifact(path: Path, protocol: dict, records: list[dict], started: float) -> None:
    artifact = {
        "protocol": protocol,
        "environment": {
            "python": platform.python_version(),
            "networkx": nx.__version__,
            "numpy": np.__version__,
            "hostname": platform.node(),
            "cpu_count": os.cpu_count(),
        },
        "source_sha256": source_manifest(protocol),
        "records": records,
        "summary": summarize(records) if records else {},
        "elapsed_s": time.perf_counter() - started,
    }
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, help="smoke-test only; invalidates confirmation")
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text())
    verify_protocol(protocol)
    expected = [
        (regime, seed)
        for regime in protocol["regimes"]
        for seed in range(protocol["graph_seed_start"], protocol["graph_seed_stop"])
    ]
    if args.limit is not None:
        expected = expected[: args.limit]
        protocol = {**protocol, "status": "smoke-test", "smoke_limit": args.limit}

    records = []
    if args.output.exists():
        existing = json.loads(args.output.read_text())
        if existing.get("protocol") != protocol:
            raise RuntimeError("existing output protocol does not match")
        records = existing.get("records", [])
    completed = {(item["regime"], item["graph_seed"]) for item in records}
    started = time.perf_counter()
    for regime, graph_seed in expected:
        if (regime, graph_seed) in completed:
            continue
        record = evaluate_graph(regime, graph_seed, protocol)
        records.append(record)
        write_artifact(args.output, protocol, records, started)
        print(
            f"{len(records):03d}/{len(expected):03d} {regime:14s} seed={graph_seed}: "
            f"{record['baseline_gap_bits']:.6g} -> {record['graft_gap_bits']:.6g} bits",
            flush=True,
        )
    write_artifact(args.output, protocol, records, started)
    print(json.dumps(summarize(records), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
