"""Frozen component ablation for SE--NNI-fast on the five HSBM regimes."""
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

from run_nni_benchmark import PROTOCOL, hierarchical_sbm
from selib.htree import (
    _external_inits,
    _graph_arrays,
    annotate,
    build_tree,
    hd_se,
    linkage_to_tree,
    refine_nni,
    refine_nni_compound,
)
from selib.se import se_agglomerative


def candidate_trees(graph, seed):
    _, _, n, _, _, _ = _graph_arrays(graph)
    candidates = [("SE-agglomerative", linkage_to_tree(
        se_agglomerative(graph), n
    ))]
    candidates.append(("recursive-SE", build_tree(
        graph, seed=seed, starts=4
    )))
    for index, linkage in enumerate(_external_inits(graph, n)):
        candidates.append((
            "Paris" if index == 0 else f"external-{index}",
            linkage_to_tree(linkage, n),
        ))
    return candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument(
        "--regimes",
        default="clean,noisy,imbalanced,weighted,weak-hierarchy",
    )
    parser.add_argument("--output", default="results/nni_ablation.json")
    args = parser.parse_args()
    regimes = args.regimes.split(",")
    records = []
    for regime in regimes:
        for seed in range(args.seeds):
            graph, _, _, _ = hierarchical_sbm(regime, seed)
            graph = nx.convert_node_labels_to_integers(graph)
            _, _, _, adj, deg, vol = _graph_arrays(graph)
            paths = []
            for name, root in candidate_trees(graph, seed):
                annotate(root, deg, adj, vol)
                raw_h = hd_se(root, vol)
                one = refine_nni(root, deg, adj, vol)
                annotate(one, deg, adj, vol)
                one_h = hd_se(one, vol)
                two = refine_nni_compound(
                    one, deg, adj, vol,
                    max_rounds=PROTOCOL["compound"]["rounds"],
                    beam_width=PROTOCOL["compound"]["beam_width"],
                    barrier_bits=PROTOCOL["compound"]["barrier_bits"],
                )
                annotate(two, deg, adj, vol)
                paths.append({
                    "initializer": name,
                    "raw_h": raw_h,
                    "nni1_h": one_h,
                    "nni2_h": hd_se(two, vol),
                })
            agg = next(row for row in paths
                       if row["initializer"] == "SE-agglomerative")
            variants = {
                "SE-agglomerative": agg["raw_h"],
                "SE-agglomerative+NNI": agg["nni1_h"],
                "Multi-start": min(row["raw_h"] for row in paths),
                "Multi-start+NNI": min(row["nni1_h"] for row in paths),
                "Multi-start+NNI+compound": min(
                    row["nni2_h"] for row in paths
                ),
            }
            for variant, entropy in variants.items():
                records.append({
                    "dataset": regime,
                    "seed": seed,
                    "variant": variant,
                    "h": entropy,
                })
            print(
                f"[{regime} seed={seed}] "
                f"raw={variants['SE-agglomerative']:.5f} "
                f"full={variants['Multi-start+NNI+compound']:.5f}",
                flush=True,
            )
    with open(args.output, "w") as handle:
        json.dump({
            "protocol": {
                "base": "tamc-nni-v1",
                "seeds": args.seeds,
                "regimes": regimes,
                "compound": PROTOCOL["compound"],
            },
            "records": records,
        }, handle, indent=2)
    print(f"WROTE {args.output} ({len(records)} records)")


if __name__ == "__main__":
    main()
