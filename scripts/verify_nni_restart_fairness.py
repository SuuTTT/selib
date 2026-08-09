"""Verify the sealed candidate-budget restart audit from raw records.

The checker intentionally recomputes selection, gaps, hit counts, schedules,
and summaries from candidate-level evidence.  It does not import the runner,
so a shared implementation mistake cannot make the audit self-confirming.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path


TOL = 1e-9
REGIMES = ("clean", "noisy", "imbalanced", "weighted", "weak-hierarchy")
FULL_METHODS = (
    "NEST-R32",
    "NEST-coalescent-B32",
    "HCSE-B32",
    "BBM-oracle-B32",
    "BBM-label-free-B32",
    "HCSE-time-matched-to-NEST-R32",
    "BBM-oracle-time-matched-to-NEST-R32",
    "BBM-label-free-time-matched-to-NEST-R32",
    "SE-agglomerative",
    "Louvain-2L",
)
SEALED_HEADLINES = {
    "NEST-R32": (250, 0, 249),
    "NEST-coalescent-B32": (250, 0, 249),
    "HCSE-B32": (250, 0, 2),
    "BBM-oracle-B32": (248, 2, 1),
    "BBM-label-free-B32": (250, 0, 1),
    "SE-agglomerative": (250, 0, 44),
    "Louvain-2L": (250, 0, 0),
}


def close(left: float, right: float, tol: float = TOL) -> bool:
    return math.isclose(float(left), float(right), rel_tol=tol, abs_tol=tol)


def expected_relative_gap(entropy: float, optimum: float) -> float:
    return max(0.0, entropy - optimum) / max(abs(optimum), 1e-12) * 100.0


def verify_outcome(outcome: dict, optimum: float, location: str) -> None:
    status = outcome.get("status", "ok")
    if status == "failed":
        assert outcome["entropy_bits"] is None, location
        assert outcome["additive_gap_bits"] is None, location
        assert outcome["relative_gap_percent"] is None, location
        assert not outcome["globally_optimal"], location
        assert outcome["successful_candidate_calls"] == 0, location
        return

    entropy = float(outcome["entropy_bits"])
    assert math.isfinite(entropy), location
    assert entropy + TOL >= optimum, (
        f"{location}: candidate {entropy} beats exact optimum {optimum}"
    )
    assert close(outcome["additive_gap_bits"], max(0.0, entropy - optimum)), location
    assert close(
        outcome["relative_gap_percent"], expected_relative_gap(entropy, optimum)
    ), location
    assert bool(outcome["globally_optimal"]) == close(entropy, optimum), location


def verify_candidate_method(outcome: dict, optimum: float, location: str) -> None:
    candidates = outcome["candidates"]
    assert outcome["candidate_calls"] == len(candidates), location
    successful = [candidate for candidate in candidates if "entropy_bits" in candidate]
    assert outcome["successful_candidate_calls"] == len(successful), location
    assert outcome["failed_candidate_calls"] == len(candidates) - len(successful), location
    assert close(outcome["total_time_s"], sum(x["time_s"] for x in candidates)), location
    unique = len({round(float(x["entropy_bits"]), 10) for x in successful})
    assert outcome["unique_entropies_1e-10"] == unique, location
    if successful:
        best = min(float(x["entropy_bits"]) for x in successful)
        assert close(outcome["entropy_bits"], best), location
        assert close(outcome["selected_candidate"]["entropy_bits"], best), location
    verify_outcome(outcome, optimum, location)


def verify_summary(artifact: dict) -> None:
    records = artifact["records"]
    for method, summary in artifact["summary"].items():
        outcomes = [row["outcomes"][method] for row in records]
        successful = [
            outcome
            for outcome in outcomes
            if outcome.get("status", "ok") == "ok"
            and math.isfinite(outcome["relative_gap_percent"])
        ]
        assert summary["instances"] == len(outcomes), method
        assert summary["successful_instances"] == len(successful), method
        assert summary["failed_instances"] == len(outcomes) - len(successful), method
        assert summary["globally_optimal"] == sum(
            bool(outcome["globally_optimal"]) for outcome in outcomes
        ), method
        mean_gap = sum(x["relative_gap_percent"] for x in successful) / len(successful)
        assert close(summary["mean_relative_gap_percent"]["mean"], mean_gap), method
        assert close(
            summary["max_relative_gap_percent"],
            max(x["relative_gap_percent"] for x in successful),
        ), method

    for method, expected in SEALED_HEADLINES.items():
        summary = artifact["summary"][method]
        observed = (
            summary["successful_instances"],
            summary["failed_instances"],
            summary["globally_optimal"],
        )
        assert observed == expected, f"sealed headline changed for {method}: {observed}"


def verify(path: Path) -> dict:
    artifact = json.loads(path.read_text())
    protocol = artifact["protocol"]
    assert protocol["version"] == "tamc-nest-restart-fairness-v1"
    assert protocol["candidate_budget"] == 32
    assert protocol["frozen_selected_budget"] == 32
    assert protocol["graph_seeds"] == [160, 209]
    assert protocol["independent_regime_seeds"] is True
    assert protocol["bbm_label_free_k_grid"] == list(range(2, 9))

    records = artifact["records"]
    assert len(records) == 250
    keys = [(row["regime"], row["graph_seed"]) for row in records]
    assert len(set(keys)) == 250
    assert Counter(row["regime"] for row in records) == Counter({name: 50 for name in REGIMES})
    for regime in REGIMES:
        seeds = sorted(row["graph_seed"] for row in records if row["regime"] == regime)
        assert seeds == list(range(160, 210)), regime

    for row in records:
        label = f"{row['regime']}/seed-{row['graph_seed']}"
        optimum = float(row["global_optimum_bits"])
        assert row["manifest"]["independent_regime_seed"] is True, label
        assert set(row["outcomes"]) == set(FULL_METHODS), label

        nest = row["outcomes"]["NEST-R32"]
        nest_candidates = nest["candidate_entropies"]
        assert len(nest_candidates) == 35, label
        random_names = [name for name in nest_candidates if name.startswith("random-coalescent-")]
        assert len(random_names) == 32, label
        assert close(nest["entropy_bits"], min(nest_candidates.values())), label
        verify_outcome(nest, optimum, f"{label}/NEST-R32")

        coal = row["outcomes"]["NEST-coalescent-B32"]
        assert coal["candidate_calls"] == len(coal["candidate_entropies"]) == 32, label
        assert close(coal["entropy_bits"], min(coal["candidate_entropies"])), label
        assert nest["entropy_bits"] <= coal["entropy_bits"] + TOL, label
        verify_outcome(coal, optimum, f"{label}/NEST-coalescent-B32")

        for method in ("HCSE-B32", "BBM-oracle-B32", "BBM-label-free-B32"):
            outcome = row["outcomes"][method]
            assert len(outcome["candidates"]) == 32, f"{label}/{method}"
            verify_candidate_method(outcome, optimum, f"{label}/{method}")

        heights = Counter(
            candidate["target_height"]
            for candidate in row["outcomes"]["HCSE-B32"]["candidates"]
        )
        assert heights == Counter({2: 8, 3: 8, 4: 8, 5: 8}), label
        assert {candidate["k"] for candidate in row["outcomes"]["BBM-oracle-B32"]["candidates"]} == {6}, label
        label_free_k = [
            candidate["k"]
            for candidate in row["outcomes"]["BBM-label-free-B32"]["candidates"]
        ]
        assert label_free_k == [2, 3, 4, 5, 6, 7, 8] * 4 + [2, 3, 4, 5], label

        for prefix, full in (
            ("HCSE-time-matched-to-NEST-R32", "HCSE-B32"),
            ("BBM-oracle-time-matched-to-NEST-R32", "BBM-oracle-B32"),
            ("BBM-label-free-time-matched-to-NEST-R32", "BBM-label-free-B32"),
        ):
            outcome = row["outcomes"][prefix]
            full_candidates = row["outcomes"][full]["candidates"]
            assert outcome["candidates"] == full_candidates[: outcome["candidate_calls"]], label
            assert outcome["candidate_calls"] >= 1, label
            if outcome["candidate_calls"] > 1:
                assert outcome["prefix_time_s"] <= outcome["wall_budget_s"] + TOL, label
            verify_candidate_method(outcome, optimum, f"{label}/{prefix}")

        for method in ("SE-agglomerative", "Louvain-2L"):
            assert row["outcomes"][method]["candidate_calls"] == 1, label
            verify_outcome(row["outcomes"][method], optimum, f"{label}/{method}")

    verify_summary(artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "artifact", nargs="?", default="results/nni_restart_fairness.json"
    )
    args = parser.parse_args()
    artifact = verify(Path(args.artifact))
    print(
        "verified 250 sealed graphs, 32 candidates per restarted comparator; "
        f"NEST exact on {artifact['summary']['NEST-coalescent-B32']['globally_optimal']}/250"
    )


if __name__ == "__main__":
    main()
