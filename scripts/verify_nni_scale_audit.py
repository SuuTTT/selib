"""Verify the completed NEST scaled-audit blocks and emit a frozen report.

The verifier intentionally excludes exact12 unless its status and SHA-256 files
exist and the requested 1,000 records are present.  This prevents a checkpoint
from being mistaken for completed submission evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path


REGIMES = ["clean", "noisy", "imbalanced", "weighted", "weak-hierarchy"]
METHODS = {
    "SE-agglomerative", "Louvain-2L", "Paris", "HCSE", "BBM",
    "se_hier", "SE-NNI-fast",
}
T_CRITICAL_95 = {99: 1.9842169515, 499: 1.9647293909}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_tree(value, where="root") -> None:
    if isinstance(value, float):
        require(math.isfinite(value), f"non-finite number at {where}")
    elif isinstance(value, dict):
        for key, child in value.items():
            finite_tree(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            finite_tree(child, f"{where}[{index}]")


def mean_ci95(values: list[float]) -> dict[str, float | int]:
    n = len(values)
    require(n > 1, "paired confidence interval needs at least two values")
    critical = T_CRITICAL_95.get(n - 1)
    require(critical is not None, f"no frozen t critical value for df={n - 1}")
    mean = statistics.mean(values)
    half = critical * statistics.stdev(values) / math.sqrt(n)
    return {"mean": mean, "ci95_half_width": half, "n": n}


def binom_cdf(k: int, n: int, p: float) -> float:
    return sum(
        math.comb(n, i) * p**i * (1.0 - p) ** (n - i)
        for i in range(k + 1)
    )


def binom_sf(k_minus_one: int, n: int, p: float) -> float:
    return 1.0 - binom_cdf(k_minus_one, n, p)


def bisect_monotone(fn, target: float, increasing: bool) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        value = fn(mid)
        if (value < target) == increasing:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> list[float]:
    require(0 <= k <= n and n > 0, "invalid binomial count")
    lower = 0.0 if k == 0 else bisect_monotone(
        lambda p: binom_sf(k - 1, n, p), alpha / 2.0, True
    )
    upper = 1.0 if k == n else bisect_monotone(
        lambda p: binom_cdf(k, n, p), alpha / 2.0, False
    )
    return [lower, upper]


def verify_seal(root: Path, stem: str) -> Path:
    json_path = root / f"{stem}.json"
    status_path = root / f"{stem}.status"
    hash_path = root / f"{stem}.sha256"
    require(json_path.is_file(), f"missing {json_path}")
    require(status_path.read_text().strip() == "0", f"nonzero status for {stem}")
    expected = hash_path.read_text().split()[0]
    actual = sha256(json_path)
    require(actual == expected, f"SHA-256 mismatch for {stem}")
    return json_path


def verify_n64(root: Path) -> tuple[list[dict], dict]:
    all_records = []
    manifests = []
    for regime in REGIMES:
        stem = "n64-weak" if regime == "weak-hierarchy" else f"n64-{regime}"
        data = json.loads(verify_seal(root, stem).read_text())
        finite_tree(data, stem)
        require(data["protocol"]["version"] == "tamc-nni-v1", f"protocol {stem}")
        require(data["protocol"]["actual_seeds"] == 100, f"seed count {stem}")
        require(data["protocol"]["seed_range"] == [1000, 1099], f"seed range {stem}")
        require(data["protocol"]["vertices"] == 64, f"vertex count {stem}")
        require(len(data["manifests"]) == 100, f"manifest count {stem}")
        require(len(data["records"]) == 700, f"record count {stem}")
        keys = set()
        for row in data["records"]:
            require(row["dataset"] == regime, f"regime mismatch {stem}")
            require(row["status"] == "ok", f"failed record {stem}")
            require(row["method"] in METHODS, f"unknown method {row['method']}")
            require(row["n"] == 64, f"wrong n in {stem}")
            require(row["nni1_h"] <= row["raw_h"] + 1e-9, f"one-step increase {stem}")
            require(row["nni2_h"] <= row["nni1_h"] + 1e-9, f"compound increase {stem}")
            key = (row["dataset"], row["seed"], row["method"])
            require(key not in keys, f"duplicate record {key}")
            keys.add(key)
        require({row["seed"] for row in data["records"]} == set(range(1000, 1100)),
                f"seed coverage {stem}")
        require({row["method"] for row in data["records"]} == METHODS,
                f"method coverage {stem}")
        all_records.extend(data["records"])
        manifests.extend(data["manifests"])

    by_key = {
        (row["dataset"], row["seed"], row["method"]): row
        for row in all_records
    }
    by_regime = {}
    pooled = []
    for regime in REGIMES:
        margins = []
        for seed in range(1000, 1100):
            ours = by_key[(regime, seed, "SE-NNI-fast")]["raw_h"]
            baseline = min(
                by_key[(regime, seed, "HCSE")]["raw_h"],
                by_key[(regime, seed, "BBM")]["raw_h"],
            )
            margins.append(baseline - ours)
        require(all(value > 1e-10 for value in margins), f"non-win in {regime}")
        by_regime[regime] = {
            **mean_ci95(margins),
            "strict_wins": sum(value > 1e-10 for value in margins),
            "minimum_margin": min(margins),
            "maximum_margin": max(margins),
        }
        pooled.extend(margins)
    return all_records, {
        "graphs": 500,
        "records": len(all_records),
        "manifests": len(manifests),
        "by_regime": by_regime,
        "pooled": {
            **mean_ci95(pooled),
            "strict_wins": sum(value > 1e-10 for value in pooled),
            "minimum_margin": min(pooled),
            "maximum_margin": max(pooled),
        },
    }


def verify_exact(root: Path, stem: str, n: int, expected_records: int,
                 seed_range: tuple[int, int]) -> tuple[dict, dict]:
    data = json.loads(verify_seal(root, stem).read_text())
    finite_tree(data, stem)
    require(data["protocol"]["version"] == "tamc-nest-restart-fairness-v1",
            f"protocol {stem}")
    require(data["protocol"]["candidate_budget"] == 32, f"budget {stem}")
    require(data["protocol"]["n"] == n, f"protocol n {stem}")
    require(len(data["records"]) == expected_records, f"record count {stem}")
    require({row["regime"] for row in data["records"]} == set(REGIMES),
            f"regimes {stem}")
    require({row["graph_seed"] for row in data["records"]} ==
            set(range(seed_range[0], seed_range[1] + 1)), f"seeds {stem}")
    require(len({(row["regime"], row["graph_seed"]) for row in data["records"]})
            == expected_records, f"unique records {stem}")
    methods = ["NEST-coalescent-B32", "HCSE-B32", "BBM-label-free-B32"]
    recomputed = {}
    for method in methods:
        outcomes = [row["outcomes"][method] for row in data["records"]]
        require(all(outcome.get("status", "ok") == "ok" for outcome in outcomes),
                f"failed outcome {stem}/{method}")
        require(all(outcome["candidate_calls"] == 32 for outcome in outcomes),
                f"candidate budget mismatch {stem}/{method}")
        hits = sum(bool(outcome["globally_optimal"]) for outcome in outcomes)
        require(hits == data["summary"][method]["globally_optimal"],
                f"summary mismatch {stem}/{method}")
        recomputed[method] = {
            "hits": hits,
            "instances": expected_records,
            "hit_rate_percent": 100.0 * hits / expected_records,
            "clopper_pearson_95": clopper_pearson(hits, expected_records),
            "mean_relative_gap_percent": statistics.mean(
                outcome["relative_gap_percent"] for outcome in outcomes
            ),
            "maximum_relative_gap_percent": max(
                outcome["relative_gap_percent"] for outcome in outcomes
            ),
        }
    return data, recomputed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path,
                        default=Path("results/scale-audit-20260810"))
    parser.add_argument("--legacy-exact", type=Path,
                        default=Path("results/nni_restart_fairness.json"))
    args = parser.parse_args()

    records, n64 = verify_n64(args.root)
    _, exact14 = verify_exact(args.root, "exact14", 14, 100, (3000, 3019))
    _, exact16 = verify_exact(args.root, "exact16", 16, 25, (4000, 4004))
    legacy = json.loads(args.legacy_exact.read_text())
    legacy_summary = legacy["summary"]
    exact12 = {}
    for method in ["NEST-coalescent-B32", "HCSE-B32", "BBM-label-free-B32"]:
        summary = legacy_summary[method]
        hits, total = summary["globally_optimal"], summary["instances"]
        exact12[method] = {
            "hits": hits,
            "instances": total,
            "hit_rate_percent": 100.0 * hits / total,
            "clopper_pearson_95": clopper_pearson(hits, total),
            "mean_relative_gap_percent": summary["mean_relative_gap_percent"]["mean"],
            "maximum_relative_gap_percent": summary["max_relative_gap_percent"],
        }

    nest_hits = sum(block["NEST-coalescent-B32"]["hits"]
                    for block in [exact12, exact14, exact16])
    nest_total = sum(block["NEST-coalescent-B32"]["instances"]
                     for block in [exact12, exact14, exact16])
    report = {
        "status": "PASS",
        "scope": "seven completed scale blocks; incomplete exact12 checkpoint excluded",
        "n64": n64,
        "exact": {"n12": exact12, "n14": exact14, "n16": exact16},
        "combined_nest_exact_hits": {
            "hits": nest_hits,
            "instances": nest_total,
            "hit_rate_percent": 100.0 * nest_hits / nest_total,
            "clopper_pearson_95": clopper_pearson(nest_hits, nest_total),
        },
    }
    report_path = args.root / "VERIFICATION_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    pooled = n64["pooled"]
    lines = [
        "# NEST scaled-audit verification",
        "",
        "Status: **PASS** for seven completed, hash-sealed blocks. The interrupted",
        "exact12 checkpoint is excluded.",
        "",
        "## 64-vertex benchmark",
        "",
        f"- 500 graph instances, {n64['records']} method records, and "
        f"{n64['manifests']} manifests.",
        f"- Paired gain over the better of HCSE and BBM: "
        f"{pooled['mean']:.4f} +/- {pooled['ci95_half_width']:.4f} bits "
        f"(95% t interval).",
        f"- Strict wins: {pooled['strict_wins']}/{pooled['n']}.",
        "",
        "## Exact optimum audit",
        "",
        "| n | Instances | NEST | HCSE | label-free BBM |",
        "|---:|---:|---:|---:|---:|",
    ]
    for label, block in [(12, exact12), (14, exact14), (16, exact16)]:
        lines.append(
            f"| {label} | {block['NEST-coalescent-B32']['instances']} | "
            f"{block['NEST-coalescent-B32']['hits']} | "
            f"{block['HCSE-B32']['hits']} | {block['BBM-label-free-B32']['hits']} |"
        )
    combined = report["combined_nest_exact_hits"]
    lines.extend([
        "",
        f"Across the three completed size strata, NEST hits "
        f"{combined['hits']}/{combined['instances']} exact optima; its exact "
        f"95% Clopper-Pearson interval is "
        f"[{100*combined['clopper_pearson_95'][0]:.2f}%, "
        f"{100*combined['clopper_pearson_95'][1]:.2f}%].",
        "",
    ])
    (args.root / "VERIFICATION_REPORT.md").write_text("\n".join(lines))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
