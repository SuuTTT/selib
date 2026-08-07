"""Fail closed on incomplete, unpaired, or non-monotone benchmark artifacts."""
import argparse
import json
from collections import Counter


METHODS = {
    "SE-agglomerative", "Louvain-2L", "Paris", "HCSE", "BBM",
    "se_hier", "SE-NNI-fast",
}
REGIMES = {"clean", "noisy", "imbalanced", "weighted", "weak-hierarchy"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="results/nni_benchmark.json")
    parser.add_argument("--seeds", type=int, default=10)
    args = parser.parse_args()
    data = json.load(open(args.path))
    records = data["records"]

    expected = len(METHODS) * len(REGIMES) * args.seeds
    assert len(records) == expected, (len(records), expected)
    assert len(data["manifests"]) == len(REGIMES) * args.seeds
    keys = Counter()
    for record in records:
        key = (record["dataset"], record["seed"], record["method"])
        keys[key] += 1
        assert record["dataset"] in REGIMES
        assert record["method"] in METHODS
        assert record["status"] == "ok", record
        assert record["nni1_h"] <= record["raw_h"] + 1e-9, record
        assert record["nni2_h"] <= record["nni1_h"] + 1e-9, record
        assert 0.0 <= record["raw_fine_purity"] <= 1.0
        assert 0.0 <= record["final_fine_purity"] <= 1.0
        assert record["constructor_time_s"] >= 0.0
    assert all(count == 1 for count in keys.values())
    assert len(keys) == expected

    summary_keys = Counter(
        (entry["dataset"], entry["method"]) for entry in data["summary"]
    )
    assert len(summary_keys) == len(METHODS) * len(REGIMES)
    assert all(count == 1 for count in summary_keys.values())
    print(
        f"VERIFIED {expected} unique paired records, "
        f"{len(data['manifests'])} manifests, monotone NNI endpoints"
    )


if __name__ == "__main__":
    main()
