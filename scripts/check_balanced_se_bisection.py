"""Finite verification of the balanced regular-graph SE/bisection identity.

For a loop-free d-regular graph on an even number of vertices, every balanced
two-module partition has module volumes vol(G)/2. Its two-dimensional
structural entropy is therefore an affine, strictly increasing function of the
cut weight. This dependency-free script checks the closed form against a direct
implementation of the canonical 2D-SE definition on several regular families.

The calculation is a regression/falsification aid, not a proof of NP-hardness.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

Edge = tuple[int, int, float]


def balanced_partitions(n: int):
    """Yield each unordered balanced bipartition once, with vertex 0 on side 0."""
    if n % 2:
        raise ValueError("balanced bisection requires even n")
    for left_tail in itertools.combinations(range(1, n), n // 2 - 1):
        left = {0, *left_tail}
        yield [0 if vertex in left else 1 for vertex in range(n)]


def normalize_edges(pairs) -> list[Edge]:
    edges = set()
    for u, v in pairs:
        if u == v:
            continue
        edges.add((min(u, v), max(u, v)))
    return [(u, v, 1.0) for u, v in sorted(edges)]


def degrees(n: int, edges: list[Edge]) -> list[float]:
    out = [0.0] * n
    for u, v, weight in edges:
        out[u] += weight
        out[v] += weight
    return out


def cut_weight(edges: list[Edge], labels: list[int]) -> float:
    return sum(weight for u, v, weight in edges if labels[u] != labels[v])


def canonical_entropy(n: int, edges: list[Edge], labels: list[int]) -> float:
    """Direct canonical 2D structural entropy, independent of selib code."""
    deg = degrees(n, edges)
    total_volume = sum(deg)
    volumes = [sum(deg[v] for v in range(n) if labels[v] == side) for side in (0, 1)]
    cuts = [0.0, 0.0]
    for u, v, weight in edges:
        if labels[u] != labels[v]:
            cuts[labels[u]] += weight
            cuts[labels[v]] += weight

    entropy = 0.0
    for vertex, degree in enumerate(deg):
        volume = volumes[labels[vertex]]
        if degree > 0:
            entropy -= degree / total_volume * math.log2(degree / volume)
    for side in (0, 1):
        if cuts[side] > 0:
            entropy -= cuts[side] / total_volume * math.log2(
                volumes[side] / total_volume
            )
    return entropy


def predicted_entropy(n: int, edges: list[Edge], cut: float) -> float:
    """Closed form for a balanced bipartition of a regular graph."""
    deg = degrees(n, edges)
    total_volume = sum(deg)
    total_edge_weight = total_volume / 2.0
    constant = -sum(
        degree * math.log2(degree) for degree in deg if degree > 0
    ) / total_volume
    internal_weight = total_edge_weight - cut
    return (
        constant
        + (2.0 * internal_weight / total_volume) * math.log2(total_volume / 2.0)
        + (2.0 * cut / total_volume) * math.log2(total_volume)
    )


def validate_graph(name: str, n: int, edges: list[Edge]) -> dict:
    deg = degrees(n, edges)
    if not n or n % 2 or min(deg) <= 0 or len(set(deg)) != 1:
        raise ValueError(f"{name} is not a positive-degree regular even-order graph")

    records = []
    max_error = 0.0
    for labels in balanced_partitions(n):
        cut = cut_weight(edges, labels)
        observed = canonical_entropy(n, edges, labels)
        predicted = predicted_entropy(n, edges, cut)
        max_error = max(max_error, abs(observed - predicted))
        records.append((cut, observed))

    min_cut = min(cut for cut, _ in records)
    min_entropy = min(entropy for _, entropy in records)
    entropy_minimizer_cuts = [
        cut for cut, entropy in records if abs(entropy - min_entropy) <= 1e-12
    ]
    ordering_ok = all(abs(cut - min_cut) <= 1e-12 for cut in entropy_minimizer_cuts)

    edge_weight = sum(weight for _, _, weight in edges)
    base_cut, base_entropy = min(records, key=lambda item: item[0])
    slope_errors = [
        abs((entropy - base_entropy) - (cut - base_cut) / edge_weight)
        for cut, entropy in records
    ]

    return {
        "name": name,
        "n": n,
        "degree": deg[0],
        "edges": len(edges),
        "balanced_partitions": len(records),
        "minimum_cut": min_cut,
        "minimum_entropy_bits": min_entropy,
        "max_formula_error": max_error,
        "max_affine_slope_error": max(slope_errors, default=0.0),
        "entropy_minimizers_are_minimum_bisections": ordering_ok,
    }


def cycle(n: int) -> list[Edge]:
    return normalize_edges((vertex, (vertex + 1) % n) for vertex in range(n))


def complete(n: int) -> list[Edge]:
    return normalize_edges(itertools.combinations(range(n), 2))


def complete_bipartite(k: int) -> list[Edge]:
    return normalize_edges((left, k + right) for left in range(k) for right in range(k))


def prism(k: int) -> list[Edge]:
    pairs = []
    for layer in (0, 1):
        offset = layer * k
        pairs.extend((offset + i, offset + (i + 1) % k) for i in range(k))
    pairs.extend((i, k + i) for i in range(k))
    return normalize_edges(pairs)


def mobius_ladder(n: int) -> list[Edge]:
    pairs = [(i, (i + 1) % n) for i in range(n)]
    pairs.extend((i, i + n // 2) for i in range(n // 2))
    return normalize_edges(pairs)


def circulant(n: int, steps: tuple[int, ...]) -> list[Edge]:
    return normalize_edges(
        (vertex, (vertex + step) % n)
        for vertex in range(n)
        for step in steps
    )


def graph_suite() -> list[tuple[str, int, list[Edge]]]:
    suite = []
    for n in (4, 6, 8, 10, 12):
        suite.append((f"cycle-{n}", n, cycle(n)))
    for n in (4, 6, 8):
        suite.append((f"complete-{n}", n, complete(n)))
    for k in (2, 3, 4, 5, 6):
        suite.append((f"complete-bipartite-{k}-{k}", 2 * k, complete_bipartite(k)))
    for k in (3, 4, 5, 6):
        suite.append((f"prism-{k}", 2 * k, prism(k)))
    for n in (8, 10, 12):
        suite.append((f"mobius-ladder-{n}", n, mobius_ladder(n)))
        suite.append((f"circulant-1-2-{n}", n, circulant(n, (1, 2))))
    return suite


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    records = [validate_graph(name, n, edges) for name, n, edges in graph_suite()]
    summary = {
        "protocol": "balanced-regular-2d-se-bisection-v1",
        "evaluator": "dependency-free canonical 2D-SE formula",
        "identity": "H2(P)-H2(P0)=(cut(P)-cut(P0))/|E|",
        "graphs": len(records),
        "balanced_partitions": sum(row["balanced_partitions"] for row in records),
        "max_formula_error": max(row["max_formula_error"] for row in records),
        "max_affine_slope_error": max(
            row["max_affine_slope_error"] for row in records
        ),
        "ordering_failures": sum(
            not row["entropy_minimizers_are_minimum_bisections"] for row in records
        ),
        "records": records,
    }
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
