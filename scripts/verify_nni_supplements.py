"""Verify the real-network, scaling, and ablation evidence artifacts."""
import argparse
import json
import math


def finite(record, fields):
    for field in fields:
        assert field in record, (field, record)
        assert math.isfinite(float(record[field])), (field, record[field])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", default="results/nni_benchmark.json")
    parser.add_argument("--real", default="results/nni_real_benchmark.json")
    parser.add_argument("--scaling", default="results/nni_scaling.json")
    parser.add_argument("--ablation", default="results/nni_ablation.json")
    args = parser.parse_args()

    main_records = json.load(open(args.main))["records"]
    main_ours = {
        (row["dataset"], row["seed"]): row["raw_h"]
        for row in main_records
        if row.get("status") == "ok" and row["method"] == "SE-NNI-fast"
    }

    real = json.load(open(args.real))["records"]
    real = [row for row in real if row.get("status") == "ok"]
    assert len(real) == 28
    assert len({(row["dataset"], row["method"]) for row in real}) == 28
    for row in real:
        finite(row, ["raw_h", "nni1_h", "nni2_h"])
        assert row["nni1_h"] <= row["raw_h"] + 1e-9
        assert row["nni2_h"] <= row["nni1_h"] + 1e-9
    for dataset in {row["dataset"] for row in real}:
        rows = [row for row in real if row["dataset"] == dataset]
        ours = next(row for row in rows if row["method"] == "SE-NNI-fast")
        assert ours["raw_h"] <= min(row["raw_h"] for row in rows) + 1e-10

    scaling = json.load(open(args.scaling))["records"]
    assert len(scaling) == 24
    assert len({(row["n"], row["seed"], row["method"])
                for row in scaling}) == 24
    by_scale = {(row["n"], row["seed"], row["method"]): row
                for row in scaling}
    for n in {row["n"] for row in scaling}:
        for seed in {row["seed"] for row in scaling if row["n"] == n}:
            old = by_scale[(n, seed, "se_hier")]
            ours = by_scale[(n, seed, "SE-NNI-fast")]
            finite(old, ["h", "time_s"])
            finite(ours, ["h", "time_s"])
            assert ours["h"] < old["h"] - 1e-10

    ablation = json.load(open(args.ablation))["records"]
    assert len(ablation) == 250
    assert len({(row["dataset"], row["seed"], row["variant"])
                for row in ablation}) == 250
    full = {
        (row["dataset"], row["seed"]): row["h"]
        for row in ablation
        if row["variant"] == "Multi-start+NNI+compound"
    }
    assert full.keys() == main_ours.keys()
    for key in full:
        assert math.isclose(full[key], main_ours[key], abs_tol=1e-12)

    print(
        "VERIFIED 28 real records, 24 scaling records, 250 ablation "
        "records, and 50 full-method cross-artifact matches"
    )


if __name__ == "__main__":
    main()
