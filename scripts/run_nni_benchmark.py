"""Frozen benchmark for exact and compound NNI structural-entropy refinement.

The script compares independent hierarchy constructors, then applies the same
one-step and two-step NNI post-processor to every binary-compatible output.
All records are paired by graph seed and retain raw per-run measurements.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import os
import random
import sys
import time
import tracemalloc
from collections import defaultdict

import networkx as nx
import numpy as np
from scipy import stats

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from selib.htree import (
    TNode,
    _graph_arrays,
    annotate,
    copy_tree,
    encoding_tree,
    encoding_tree_nni_fast,
    hd_se,
    linkage_to_tree,
    refine_nni,
    refine_nni_compound,
)
from selib.se import se_agglomerative


PROTOCOL = {
    "version": "tamc-nni-v1",
    "seeds": "0..9 unless overridden for smoke testing",
    "primary_metric": "tree structural entropy H^T (lower is better)",
    "secondary_metrics": [
        "fine and coarse dendrogram purity (higher is better)",
        "constructor and refinement wall time",
        "Python allocation peak measured by tracemalloc",
    ],
    "compound": {"rounds": 8, "beam_width": 16, "barrier_bits": 0.05},
    "selection": "HCSE target height 2..5 selected by minimum H^T; BBM receives oracle fine-k",
}


def hierarchical_sbm(regime, seed, size_multiplier=1):
    """Two-level planted hierarchy with four coarse and eight fine blocks."""
    if size_multiplier < 1 or int(size_multiplier) != size_multiplier:
        raise ValueError("size_multiplier must be a positive integer")
    size_multiplier = int(size_multiplier)
    rng = np.random.default_rng(seed)
    if regime == "imbalanced":
        sizes = [4, 12, 6, 10, 5, 11, 7, 9]
    else:
        sizes = [8] * 8
    sizes = [size_multiplier * size for size in sizes]
    if regime == "clean":
        probs = (0.42, 0.12, 0.015)
    elif regime == "noisy":
        probs = (0.25, 0.14, 0.07)
    elif regime == "imbalanced":
        probs = (0.38, 0.12, 0.025)
    elif regime == "weighted":
        probs = (0.32, 0.11, 0.025)
    elif regime == "weak-hierarchy":
        probs = (0.24, 0.17, 0.045)
    else:
        raise ValueError(regime)

    fine = []
    coarse = []
    for block, size in enumerate(sizes):
        fine.extend([block] * size)
        coarse.extend([block // 2] * size)
    graph = nx.Graph()
    graph.add_nodes_from(range(len(fine)))
    for u in graph.nodes():
        for v in range(u + 1, len(fine)):
            p = probs[0] if fine[u] == fine[v] else (
                probs[1] if coarse[u] == coarse[v] else probs[2]
            )
            if rng.random() < p:
                if regime == "weighted":
                    scale = 2.0 if fine[u] == fine[v] else (
                        1.0 if coarse[u] == coarse[v] else 0.5
                    )
                    weight = float(scale * rng.lognormal(0.0, 0.25))
                else:
                    weight = 1.0
                graph.add_edge(u, v, weight=weight)

    # Preserve every generated instance while making the random-walk objective
    # well-defined on one connected graph. Tiny connector edges are recorded.
    connectors = []
    components = [sorted(component) for component in nx.connected_components(graph)]
    for left, right in zip(components, components[1:]):
        edge = (left[0], right[0], 0.01)
        graph.add_edge(edge[0], edge[1], weight=edge[2])
        connectors.append(edge)
    return graph, fine, coarse, {
        "regime": regime,
        "sizes": sizes,
        "probabilities": probs,
        "connectors": connectors,
    }


def louvain_two_level(graph, seed):
    communities = nx.community.louvain_communities(
        graph, weight="weight", seed=seed
    )
    return TNode(children=[
        TNode(children=[TNode(vertex=v) for v in sorted(community)])
        for community in communities
    ])


def dendrogram_purity(root, labels):
    """Pair-weighted dendrogram purity for one reference partition."""
    leaf_sets = {}
    leaf_nodes = {}

    def visit(node):
        if node.is_leaf():
            leaves = {node.vertex}
            leaf_nodes[node.vertex] = node
        else:
            leaves = set()
            for child in node.children:
                child.parent = node
                leaves.update(visit(child))
        leaf_sets[id(node)] = leaves
        return leaves

    root.parent = None
    visit(root)

    def lca(left, right):
        ancestors = set()
        node = left
        while node is not None:
            ancestors.add(id(node))
            node = node.parent
        node = right
        while id(node) not in ancestors:
            node = node.parent
        return node

    by_class = defaultdict(list)
    for vertex, label in enumerate(labels):
        by_class[label].append(vertex)
    numerator = 0.0
    denominator = 0
    for label, vertices in by_class.items():
        class_set = set(vertices)
        for offset, u in enumerate(vertices):
            for v in vertices[offset + 1:]:
                cluster = leaf_sets[id(lca(leaf_nodes[u], leaf_nodes[v]))]
                numerator += len(cluster & class_set) / len(cluster)
                denominator += 1
    return numerator / denominator if denominator else 1.0


def measured(callable_):
    tracemalloc.start()
    start = time.perf_counter()
    result = callable_()
    wall = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, wall, peak / (1024 * 1024)


def load_hcse(hcse_dir):
    if not hcse_dir:
        return None
    sys.path.insert(0, os.path.abspath(hcse_dir))
    sys.path.insert(0, os.path.join(
        os.path.abspath(hcse_dir),
        "hierarchical-clustering-well-clustered-graphs-main",
    ))
    import main as hcse_main  # type: ignore
    import BBM as hcse_bbm  # type: ignore
    import partition_cut  # type: ignore
    from PartitionTree import PartitionTreeNode  # type: ignore

    def new_leaf(node, node_id):
        leaf = PartitionTreeNode()
        leaf.id = node_id
        leaf.children = None
        leaf.origin_node_set = {str(node)}
        leaf.node_set = {str(node): {}}
        leaf.height = 1
        return leaf

    def convert(node):
        if not node.children:
            vertices = sorted(int(x) for x in node.origin_node_set)
            if len(vertices) == 1:
                return TNode(vertex=vertices[0])
            return TNode(children=[TNode(vertex=v) for v in vertices])
        return TNode(children=[convert(child) for child in node.children])

    def hcse(graph, target_height):
        labelled = nx.relabel_nodes(
            graph, {node: str(node) for node in graph.nodes()}, copy=True
        )
        hcse_main.id_generator = hcse_main.NewIDPartitionTreeNode(len(graph) + 1)
        with contextlib.redirect_stdout(io.StringIO()):
            tree = hcse_main.HCSE(
                labelled, target_height=target_height, type="SE"
            )
            tree = hcse_main.BalanceTree(tree)
        return convert(tree)

    def bbm(graph, k):
        labelled = nx.relabel_nodes(
            graph, {node: str(node) for node in graph.nodes()}, copy=True
        )
        with contextlib.redirect_stdout(io.StringIO()):
            clusters = partition_cut.compute_improved_partition(labelled, k)
            # The official partitioner can emit empty clusters on very small
            # graphs when k is large. Empty clusters contain no leaves and must
            # not be passed to HuffmanMerge.
            clusters = [cluster for cluster in clusters if cluster]
            if not clusters:
                clusters = [list(labelled.nodes())]
            hcse_bbm.id_generator = hcse_bbm.NewIDPartitionTreeNode(len(graph) + 1)
            roots = []
            for cluster in clusters:
                nodes = [str(v) for v in cluster]
                if len(nodes) == 1:
                    root = new_leaf(nodes[0], next(hcse_bbm.id_generator))
                else:
                    root = hcse_bbm.HuffmanMerge(labelled.subgraph(nodes).copy())
                roots.append(root)
            tree = roots[0] if len(roots) == 1 else hcse_bbm.SubHuffmanMerge(roots)
        return convert(tree)

    return hcse, bbm


def constructors(graph, seed, fine_k, hcse_api):
    _, _, n, adj, deg, vol = _graph_arrays(graph)
    out = []

    def add(name, build, metadata=None):
        try:
            random.seed(seed)
            np.random.seed(seed)
            root, wall, peak = measured(build)
            annotate(root, deg, adj, vol)
            out.append((name, root, wall, peak, metadata or {}))
        except Exception as error:  # preserve failure as a benchmark record
            out.append((name, None, None, None, {"error": repr(error)}))

    add("SE-agglomerative", lambda: linkage_to_tree(
        se_agglomerative(graph), n
    ))
    add("Louvain-2L", lambda: louvain_two_level(graph, seed))

    try:
        from sknetwork.hierarchy import Paris
        import scipy.sparse as sp

        def paris():
            matrix = nx.to_scipy_sparse_array(
                graph, nodelist=list(range(n)), weight="weight", format="csr"
            )
            matrix = sp.csr_matrix(matrix)
            matrix.indices = matrix.indices.astype(np.int32)
            matrix.indptr = matrix.indptr.astype(np.int32)
            return linkage_to_tree(Paris().fit_predict(matrix), n)

        add("Paris", paris)
    except Exception as error:
        out.append(("Paris", None, None, None, {"error": repr(error)}))

    if hcse_api:
        hcse, bbm = hcse_api

        def best_hcse():
            candidates = []
            for height in range(2, 6):
                tree = hcse(graph, height)
                annotate(tree, deg, adj, vol)
                candidates.append((hd_se(tree, vol), height, tree))
            _, _, tree = min(candidates, key=lambda item: item[0])
            return tree

        # TNode uses slots, so record the selected-height rule in protocol rather
        # than attaching it to the returned tree.
        add("HCSE", best_hcse, {"height_sweep": [2, 3, 4, 5]})
        add("BBM", lambda: bbm(graph, fine_k), {"oracle_k": fine_k})

    add("se_hier", lambda: encoding_tree(
        graph, seed=seed, starts=4, do_refine=True
    )[0])
    add("SE-NNI-fast", lambda: encoding_tree_nni_fast(
        graph, seed=seed, starts=4, compound=True
    )[0])
    return out, deg, adj, vol


def score_constructor(name, root, wall, peak, metadata, graph, labels,
                      deg, adj, vol, dataset, seed):
    if root is None:
        return {
            "dataset": dataset, "seed": seed, "method": name,
            "status": "failed", **metadata,
        }
    annotate(root, deg, adj, vol)
    raw_h = hd_se(root, vol)
    raw_fine = dendrogram_purity(root, labels["fine"])
    raw_coarse = dendrogram_purity(root, labels["coarse"])

    one, one_wall, one_peak = measured(lambda: refine_nni(
        copy_tree(root), deg, adj, vol, return_trace=True
    ))
    one_tree, one_trace = one
    annotate(one_tree, deg, adj, vol)
    one_h = hd_se(one_tree, vol)

    compound, compound_wall, compound_peak = measured(
        lambda: refine_nni_compound(
            copy_tree(one_tree), deg, adj, vol,
            max_rounds=PROTOCOL["compound"]["rounds"],
            beam_width=PROTOCOL["compound"]["beam_width"],
            barrier_bits=PROTOCOL["compound"]["barrier_bits"],
            return_trace=True,
        )
    )
    final_tree, compound_trace = compound
    annotate(final_tree, deg, adj, vol)
    final_h = hd_se(final_tree, vol)
    compound_moves = [
        step for step in compound_trace if step["kind"] == "compound"
    ]
    return {
        "dataset": dataset,
        "seed": seed,
        "method": name,
        "status": "ok",
        "n": graph.number_of_nodes(),
        "m": graph.number_of_edges(),
        "raw_h": raw_h,
        "nni1_h": one_h,
        "nni2_h": final_h,
        "nni1_gain": raw_h - one_h,
        "nni2_extra_gain": one_h - final_h,
        "nni1_moves": len(one_trace),
        "compound_moves": len(compound_moves),
        "max_barrier": max(
            (move["barrier"] for move in compound_moves), default=0.0
        ),
        "raw_fine_purity": raw_fine,
        "raw_coarse_purity": raw_coarse,
        "final_fine_purity": dendrogram_purity(final_tree, labels["fine"]),
        "final_coarse_purity": dendrogram_purity(final_tree, labels["coarse"]),
        "constructor_time_s": wall,
        "nni1_time_s": one_wall,
        "nni2_time_s": compound_wall,
        "python_peak_mib": max(peak, one_peak, compound_peak),
        **metadata,
    }


def mean_ci(values):
    values = np.asarray(values, dtype=float)
    mean = float(np.mean(values))
    if len(values) < 2:
        return {"mean": mean, "ci95": 0.0, "n": len(values)}
    sem = stats.sem(values)
    half = float(stats.t.ppf(0.975, len(values) - 1) * sem)
    return {"mean": mean, "ci95": half, "n": len(values)}


def summarize(records):
    grouped = defaultdict(list)
    for record in records:
        if record.get("status") == "ok":
            grouped[(record["dataset"], record["method"])].append(record)
    summary = []
    metrics = [
        "raw_h", "nni1_h", "nni2_h", "nni1_gain", "nni2_extra_gain",
        "raw_fine_purity", "raw_coarse_purity", "final_fine_purity",
        "final_coarse_purity", "constructor_time_s", "nni1_time_s",
        "nni2_time_s", "python_peak_mib",
    ]
    for (dataset, method), rows in sorted(grouped.items()):
        item = {"dataset": dataset, "method": method, "runs": len(rows)}
        for metric in metrics:
            item[metric] = mean_ci([row[metric] for row in rows])
        item["nni1_improved_rate"] = sum(
            row["nni1_gain"] > 1e-10 for row in rows
        ) / len(rows)
        item["compound_improved_rate"] = sum(
            row["nni2_extra_gain"] > 1e-10 for row in rows
        ) / len(rows)
        summary.append(item)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--size-multiplier", type=int, default=1)
    parser.add_argument("--output", default="results/nni_benchmark.json")
    parser.add_argument("--hcse-dir", default="external/HCSE")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--regimes",
        default="clean,noisy,imbalanced,weighted,weak-hierarchy",
    )
    args = parser.parse_args()

    hcse_api = load_hcse(args.hcse_dir) if args.hcse_dir else None
    regimes = [name.strip() for name in args.regimes.split(",") if name.strip()]
    protocol = {
        **PROTOCOL,
        "actual_seeds": args.seeds,
        "seed_range": [args.seed_start, args.seed_start + args.seeds - 1],
        "size_multiplier": args.size_multiplier,
        "vertices": 64 * args.size_multiplier,
        "checkpointing": "atomic write after every graph",
    }
    records = []
    manifests = []
    if args.resume and os.path.exists(args.output):
        with open(args.output) as handle:
            previous = json.load(handle)
        if previous.get("protocol") != protocol:
            raise ValueError("existing artifact protocol differs; refuse unsafe resume")
        records = previous.get("records", [])
        manifests = previous.get("manifests", [])
    done = {(row["dataset"], row["seed"]) for row in manifests}

    def checkpoint():
        output = {
            "protocol": protocol,
            "manifests": manifests,
            "records": records,
            "summary": summarize(records),
        }
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        temporary = args.output + ".tmp"
        with open(temporary, "w") as handle:
            json.dump(output, handle, indent=2)
        os.replace(temporary, args.output)

    for regime in regimes:
        for seed in range(args.seed_start, args.seed_start + args.seeds):
            if (regime, seed) in done:
                continue
            graph, fine, coarse, manifest = hierarchical_sbm(
                regime, seed, size_multiplier=args.size_multiplier
            )
            constructors_, deg, adj, vol = constructors(
                graph, seed, len(set(fine)), hcse_api
            )
            manifests.append({"dataset": regime, "seed": seed, **manifest})
            labels = {"fine": fine, "coarse": coarse}
            for entry in constructors_:
                record = score_constructor(
                    *entry, graph, labels, deg, adj, vol, regime, seed
                )
                records.append(record)
            ok = [r for r in records if r["dataset"] == regime
                  and r["seed"] == seed and r.get("status") == "ok"]
            best = min(ok, key=lambda row: row["nni2_h"])
            print(
                f"[{regime} seed={seed}] best={best['method']} "
                f"H={best['nni2_h']:.5f}", flush=True
            )
            checkpoint()

    checkpoint()
    print(f"WROTE {args.output} ({len(records)} records)")


if __name__ == "__main__":
    main()
