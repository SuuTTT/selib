"""Fail-closed consistency checks for the NEST basin-probability artifacts."""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.run_nni_basin_audit import HARD_N12_CASES
from selib.basin import coalescent_history_total


EXACT_COUNTS = {5: 105, 6: 945, 7: 10395, 8: 135135}
EXPECTED_MC_OPTIMAL_HITS = (1719, 1461, 2056, 4643, 3061, 807, 1775, 1786)


def close(left, right, tolerance=1e-12):
    return abs(left - right) <= tolerance


def verify_exact(path):
    artifact = json.loads(Path(path).read_text())
    assert artifact["protocol"]["version"] == "tamc-nest-basin-exact-v1"
    seen = set()
    for row in artifact["records"]:
        key = (row["regime"], row["n"])
        assert key not in seen
        seen.add(key)
        n = row["n"]
        assert n in EXACT_COUNTS
        for event in ("optimal", "strict_recovery", "both"):
            uniform = row["uniform_topology_measure"][event]
            assert uniform["topologies"] == EXACT_COUNTS[n]
            assert 0 <= uniform["successes"] <= uniform["topologies"]
            assert close(
                uniform["probability"],
                uniform["successes"] / uniform["topologies"],
            )

            weighted = row["coalescent_measure"][event]
            assert weighted["total_histories"] == coalescent_history_total(n)
            assert 0 <= weighted["successful_histories"] <= weighted["total_histories"]
            assert close(
                weighted["probability"],
                weighted["successful_histories"] / weighted["total_histories"],
            )
        assert (
            row["uniform_topology_measure"]["both"]["successes"]
            <= row["uniform_topology_measure"]["optimal"]["successes"]
        )
        assert (
            row["uniform_topology_measure"]["both"]["successes"]
            <= row["uniform_topology_measure"]["strict_recovery"]["successes"]
        )
    hard = [row for row in artifact["records"] if row["n"] == 8]
    assert len(hard) == 1
    assert hard[0]["uniform_topology_measure"]["optimal"]["successes"] == 33579
    assert hard[0]["coalescent_measure"]["optimal"]["successful_histories"] == 400655
    assert hard[0]["coalescent_measure"]["strict_recovery"]["successful_histories"] == 0
    return len(seen)


def verify_monte_carlo(path):
    artifact = json.loads(Path(path).read_text())
    protocol = artifact["protocol"]
    assert protocol["version"] == "tamc-nest-basin-monte-carlo-v1"
    starts = protocol["starts_per_graph"]
    assert starts == 10000
    seen = []
    for row in artifact["records"]:
        seen.append((row["regime"], row["graph_seed"]))
        for event in ("optimal", "strict_recovery", "both"):
            value = row["probabilities"][event]
            assert value["trials"] == starts
            assert 0 <= value["successes"] <= starts
            assert close(value["estimate"], value["successes"] / starts)
            lower, upper = value["clopper_pearson_95ci"]
            assert 0 <= lower <= value["estimate"] <= upper <= 1
        assert (
            row["probabilities"]["both"]["successes"]
            <= row["probabilities"]["optimal"]["successes"]
        )
        assert (
            row["probabilities"]["both"]["successes"]
            <= row["probabilities"]["strict_recovery"]["successes"]
        )
        optimal = row["probabilities"]["optimal"]
        expected_r32 = 1.0 - (1.0 - optimal["estimate"]) ** 32
        assert math.isclose(
            optimal["predicted_random_r32"], expected_r32,
            rel_tol=0.0, abs_tol=1e-12,
        )
    assert seen == list(HARD_N12_CASES)
    assert tuple(
        row["probabilities"]["optimal"]["successes"]
        for row in artifact["records"]
    ) == EXPECTED_MC_OPTIMAL_HITS
    assert all(
        row["probabilities"]["strict_recovery"]["successes"] == 0
        for row in artifact["records"]
    )
    return len(seen)


def main():
    exact = verify_exact("results/nni_basin_exact.json")
    monte_carlo = verify_monte_carlo("results/nni_basin_monte_carlo.json")
    print(
        f"verified {exact} exact-enumeration graphs and "
        f"{monte_carlo} Monte Carlo graphs"
    )


if __name__ == "__main__":
    main()
