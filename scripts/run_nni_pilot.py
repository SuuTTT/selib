"""Development-only gate for exact NNI refinement of ``se_hier``.

The pilot uses small CPU graphs so it can falsify the basic method quickly.
It records every run; it is not the final paper benchmark.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import networkx as nx
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from selib import datasets as D
from selib.htree import (
    encoding_tree,
    hd_se,
    refine_nni,
    top_level_labels,
)


def cases():
    for seed in range(5):
        yield "Karate", seed, D.karate
    for seed in range(10):
        yield (
            "SBM-small-clean",
            seed,
            lambda seed=seed: D.sbm(45, 3, 0.35, 0.03, seed=seed),
        )
        yield (
            "SBM-small-noisy",
            seed,
            lambda seed=seed: D.sbm(45, 3, 0.18, 0.10, seed=seed),
        )


def main():
    records = []
    for dataset, seed, loader in cases():
        graph, truth = loader()
        graph = nx.convert_node_labels_to_integers(graph)

        started = time.perf_counter()
        root, deg, adj, vol = encoding_tree(
            graph, seed=seed, starts=2, do_refine=True
        )
        build_seconds = time.perf_counter() - started
        before = hd_se(root, vol)
        before_labels = top_level_labels(root, graph.number_of_nodes())

        started = time.perf_counter()
        refined, trace = refine_nni(
            root, deg, adj, vol, return_trace=True
        )
        nni_seconds = time.perf_counter() - started
        after = hd_se(refined, vol)
        after_labels = top_level_labels(refined, graph.number_of_nodes())

        record = {
            "dataset": dataset,
            "seed": seed,
            "n": graph.number_of_nodes(),
            "m": graph.number_of_edges(),
            "h_before": before,
            "h_after": after,
            "h_gain": before - after,
            "nni_moves": len(trace),
            "build_seconds": build_seconds,
            "nni_seconds": nni_seconds,
            "nmi_before": normalized_mutual_info_score(truth, before_labels),
            "nmi_after": normalized_mutual_info_score(truth, after_labels),
            "ari_before": adjusted_rand_score(truth, before_labels),
            "ari_after": adjusted_rand_score(truth, after_labels),
        }
        records.append(record)
        print(
            f"{dataset} seed={seed}: H {before:.6f}->{after:.6f}; "
            f"moves={len(trace)}; NNI={nni_seconds:.3f}s",
            flush=True,
        )

    output = {
        "status": "development_only",
        "method": "se_hier followed by exact best-improvement rooted NNI",
        "records": records,
    }
    destination = Path("results/nni_pilot.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(f"WROTE {destination} ({len(records)} runs)")


if __name__ == "__main__":
    main()
