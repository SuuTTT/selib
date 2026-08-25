"""Label-free block proposal constructors for fixed-K SE refinement."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

import networkx as nx


def agreement_blocks(
    partitions: Iterable[Sequence[int]],
    *,
    min_size: int = 2,
):
    """Return cells on which all supplied partitions agree jointly.

    Community identifiers need not be aligned across partitions: grouping uses
    the tuple of view-specific identifiers.  Dataset truth is neither accepted
    nor required.
    """
    views = [tuple(partition) for partition in partitions]
    if len(views) < 2:
        raise ValueError("agreement blocks require at least two partitions")
    n = len(views[0])
    if any(len(view) != n for view in views):
        raise ValueError("partitions must have the same length")
    cells = defaultdict(list)
    for vertex in range(n):
        cells[tuple(view[vertex] for view in views)].append(vertex)
    return [
        tuple(vertices)
        for _, vertices in sorted(cells.items(), key=lambda item: item[0])
        if len(vertices) >= min_size
    ]


def induced_component_blocks(G, labels: Sequence[int], *, min_size: int = 2):
    """Connected pieces of each predicted community in the supplied graph."""
    nodes = list(G.nodes())
    if len(labels) != len(nodes):
        raise ValueError("labels must align with list(G.nodes())")
    position = {node: index for index, node in enumerate(nodes)}
    communities = defaultdict(list)
    for index, community in enumerate(labels):
        communities[int(community)].append(nodes[index])
    blocks = []
    for community in sorted(communities):
        subgraph = G.subgraph(communities[community])
        components = sorted(
            nx.connected_components(subgraph),
            key=lambda component: (min(position[node] for node in component), len(component)),
        )
        for component in components:
            vertices = tuple(sorted(position[node] for node in component))
            if len(vertices) >= min_size:
                blocks.append(vertices)
    return blocks


def deduplicate_blocks(blocks: Iterable[Iterable[int]]):
    """Canonical deterministic union of proposal families."""
    unique = {tuple(sorted(set(int(vertex) for vertex in block))) for block in blocks}
    unique.discard(())
    return sorted(unique, key=lambda block: (block[0], len(block), block))
