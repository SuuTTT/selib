"""Small real-network complement to the seeded hierarchical-SBM benchmark."""
import argparse
import json
import os
import sys

import networkx as nx

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from run_nni_benchmark import constructors, load_hcse, score_constructor
from selib import datasets as dataset_lib


def builtins():
    karate, karate_labels = dataset_lib.karate()
    yield "Karate", karate, karate_labels, True
    yield "Florentine", nx.florentine_families_graph(), None, False
    yield "Les-Miserables", nx.les_miserables_graph(), None, False
    yield "Davis-Southern", nx.davis_southern_women_graph(), None, False
    try:
        football, labels = dataset_lib.football()
        yield "Football", football, labels, True
    except Exception as error:
        print(f"[skip Football] {error}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/nni_real_benchmark.json")
    parser.add_argument("--hcse-dir", default="external/HCSE")
    args = parser.parse_args()
    hcse_api = load_hcse(args.hcse_dir) if args.hcse_dir else None
    records = []
    for dataset, graph, labels, labels_available in builtins():
        graph = nx.convert_node_labels_to_integers(nx.Graph(graph))
        nx.set_edge_attributes(graph, 1.0, "weight")
        if labels is None:
            fine_k = len(nx.community.louvain_communities(
                graph, weight="weight", seed=0
            ))
            labels = [0] * graph.number_of_nodes()
        else:
            fine_k = max(1, len(set(labels)))
        constructors_, deg, adj, vol = constructors(
            graph, 0, fine_k, hcse_api
        )
        label_map = {"fine": labels, "coarse": labels}
        for entry in constructors_:
            record = score_constructor(
                *entry, graph, label_map, deg, adj, vol, dataset, 0
            )
            record["labels_available"] = labels_available
            record["bbm_k_source"] = (
                "ground-truth labels" if labels_available else "Louvain count"
            )
            records.append(record)
        ok = [r for r in records if r["dataset"] == dataset
              and r.get("status") == "ok"]
        best = min(ok, key=lambda row: row["raw_h"])
        print(
            f"[{dataset}] best raw={best['method']} H={best['raw_h']:.5f}",
            flush=True,
        )
    with open(args.output, "w") as handle:
        json.dump({"records": records}, handle, indent=2)
    print(f"WROTE {args.output} ({len(records)} records)")


if __name__ == "__main__":
    main()
