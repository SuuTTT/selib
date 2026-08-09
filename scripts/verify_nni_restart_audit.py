"""Verify development, calibration, confirmation, and hard-case artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


LABELS = ("baseline", "restart_4", "restart_8", "restart_16", "restart_32")


def verify_split(split, expected_instances):
    records = split["records"]
    assert len(records) == expected_instances
    for row in records:
        optimum = row["global_optimum_bits"]
        previous = float("inf")
        for label in LABELS:
            outcome = row[label]
            entropy = outcome["entropy_bits"]
            assert entropy <= previous + 1e-9
            assert entropy >= optimum - 1e-9
            previous = entropy
    for label in LABELS:
        expected = sum(row[label]["globally_optimal"] for row in records)
        assert split["summary"][label]["globally_optimal"] == expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", default="results/nni_restart_audit.json")
    parser.add_argument(
        "--confirmation", default="results/nni_restart_confirmation.json"
    )
    parser.add_argument(
        "--independent-confirmation",
        default="results/nni_restart_independent_confirmation.json",
    )
    parser.add_argument(
        "--hard-cases", default="results/nni_restart_failure_diagnostics.json"
    )
    args = parser.parse_args()

    audit = json.loads(Path(args.audit).read_text())
    confirmation = json.loads(Path(args.confirmation).read_text())
    independent = json.loads(Path(args.independent_confirmation).read_text())
    hard_cases = json.loads(Path(args.hard_cases).read_text())

    assert audit["protocol"]["development_graph_seeds"] == [0, 9]
    assert audit["protocol"]["holdout_graph_seeds"] == [10, 59]
    assert confirmation["protocol"]["holdout_graph_seeds"] == [60, 109]
    assert independent["protocol"]["holdout_graph_seeds"] == [110, 159]
    assert independent["protocol"]["independent_regime_seeds"] is True
    verify_split(audit["development"], 50)
    verify_split(audit["holdout"], 250)
    verify_split(confirmation["holdout"], 250)
    verify_split(independent["holdout"], 250)

    assert audit["development"]["summary"]["baseline"]["globally_optimal"] == 45
    assert audit["holdout"]["summary"]["baseline"]["globally_optimal"] == 211
    assert confirmation["holdout"]["summary"]["baseline"]["globally_optimal"] == 215
    assert independent["holdout"]["summary"]["baseline"]["globally_optimal"] == 214
    assert audit["development"]["summary"]["restart_32"]["globally_optimal"] == 50
    assert audit["holdout"]["summary"]["restart_32"]["globally_optimal"] == 250
    assert confirmation["holdout"]["summary"]["restart_32"]["globally_optimal"] == 250
    assert independent["holdout"]["summary"]["restart_32"]["globally_optimal"] == 250

    assert len(hard_cases["records"]) == 60
    for case in hard_cases["summary"].values():
        assert case["budgets"]["32"]["optimal_hits"] == 20

    print(
        "VERIFIED restart audit: standard 685/800; NEST-R32 800/800; "
        "independent confirmation 250/250; hard cases 60/60 at R32"
    )


if __name__ == "__main__":
    main()
