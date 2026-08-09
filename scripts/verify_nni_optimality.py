"""Verify the exact small-graph optimality artifact and headline values."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/nni_optimality.json")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text())
    records = data["records"]
    assert len(records) == 50
    assert len({(row["regime"], row["seed"]) for row in records}) == 50
    for row in records:
        assert row["n"] == 12
        assert row["global_optimum_bits"] <= row["nest_entropy_bits"] + 1e-9
        assert row["edge_lca_lower_bound_bits"] <= row["global_optimum_bits"] + 1e-9
        expected_gap = max(
            0.0, row["nest_entropy_bits"] - row["global_optimum_bits"]
        )
        assert abs(expected_gap - row["additive_gap_bits"]) < 1e-10
        assert row["globally_optimal"] == (expected_gap <= 1e-9)
    summary = data["summary"]["overall"]
    assert summary["globally_optimal"] == 45
    assert summary["max_relative_gap_percent"] < 3.72
    assert summary["mean_relative_gap_percent"] < 0.12
    print(
        "VERIFIED 50 exact-optimum audits: "
        f"{summary['globally_optimal']}/50 optimal, "
        f"mean gap {summary['mean_relative_gap_percent']:.4f}%, "
        f"max gap {summary['max_relative_gap_percent']:.4f}%"
    )


if __name__ == "__main__":
    main()
