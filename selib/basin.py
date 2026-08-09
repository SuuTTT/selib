"""Exact and sampled basin diagnostics for rooted binary NNI search.

These helpers deliberately separate objective recovery (reaching an exact
minimum of structural entropy) from topology recovery (containing declared
planted blocks as clades).  Exhaustive topology enumeration is only practical
for very small graphs; callers should enforce an explicit size limit.
"""
from __future__ import annotations

import math
from functools import lru_cache

from .htree import TNode


# A topology is either an integer leaf or a pair of child topologies.  Child
# order is immaterial: enumeration anchors the smallest leaf in the left side
# of every split so each unordered rooted binary topology appears exactly once.


@lru_cache(maxsize=None)
def _topologies(mask: int):
    if mask <= 0:
        raise ValueError("mask must contain at least one leaf")
    if mask & (mask - 1) == 0:
        return (mask.bit_length() - 1,)

    anchor = mask & -mask
    output = []
    left = (mask - 1) & mask
    while left:
        right = mask ^ left
        if right and left & anchor:
            for left_tree in _topologies(left):
                for right_tree in _topologies(right):
                    output.append((left_tree, right_tree))
        left = (left - 1) & mask
    return tuple(output)


def rooted_binary_topologies(n: int, max_leaves: int = 8):
    """Return every unordered rooted binary topology on leaves ``0..n-1``.

    The count is ``(2n-3)!!``.  ``max_leaves`` is a deliberate memory/runtime
    guard rather than an algorithmic limitation.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if n > max_leaves:
        raise ValueError(
            f"exact topology enumeration requested for n={n}; "
            f"limit is {max_leaves}"
        )
    return _topologies((1 << n) - 1)


def topology_to_tree(topology):
    """Convert a nested topology representation to a fresh :class:`TNode`."""
    if isinstance(topology, int):
        return TNode(vertex=topology)
    left, right = topology
    return TNode(children=[topology_to_tree(left), topology_to_tree(right)])


@lru_cache(maxsize=None)
def topology_leaf_count(topology) -> int:
    if isinstance(topology, int):
        return 1
    return topology_leaf_count(topology[0]) + topology_leaf_count(topology[1])


@lru_cache(maxsize=None)
def coalescent_history_count(topology) -> int:
    """Number of pair-merge histories yielding an unordered topology.

    For child subtrees with ``a`` and ``b`` leaves, their ``a-1`` and ``b-1``
    internal merges can be interleaved in ``binom(a+b-2, a-1)`` ways before
    the final root merge.
    """
    if isinstance(topology, int):
        return 1
    left, right = topology
    left_n = topology_leaf_count(left)
    right_n = topology_leaf_count(right)
    return (
        math.comb(left_n + right_n - 2, left_n - 1)
        * coalescent_history_count(left)
        * coalescent_history_count(right)
    )


def coalescent_history_total(n: int) -> int:
    """Total unordered pair choices in the pairwise coalescent process."""
    if n <= 0:
        raise ValueError("n must be positive")
    total = 1
    for active in range(n, 1, -1):
        total *= math.comb(active, 2)
    return total


def tree_clades(root):
    """Return the descendant-leaf set of every node in ``root``."""
    clades = set()

    def visit(node):
        if node.is_leaf():
            leaves = frozenset((node.vertex,))
        else:
            leaves = frozenset().union(*(visit(child) for child in node.children))
        clades.add(leaves)
        return leaves

    visit(root)
    return clades


def planted_recovery(root, fine_blocks, coarse_blocks):
    """Check whether every declared fine/coarse block occurs as a clade.

    Singleton blocks are included and are necessarily recovered by any valid
    leaf-labeled tree.  The returned counts make this convention explicit.
    """
    clades = tree_clades(root)
    fine = [frozenset(block) for block in fine_blocks]
    coarse = [frozenset(block) for block in coarse_blocks]
    fine_hits = sum(block in clades for block in fine)
    coarse_hits = sum(block in clades for block in coarse)
    return {
        "fine_recovered": fine_hits == len(fine),
        "coarse_recovered": coarse_hits == len(coarse),
        "strict_recovered": fine_hits == len(fine) and coarse_hits == len(coarse),
        "fine_hits": fine_hits,
        "fine_total": len(fine),
        "fine_nontrivial_total": sum(len(block) > 1 for block in fine),
        "coarse_hits": coarse_hits,
        "coarse_total": len(coarse),
        "coarse_nontrivial_total": sum(len(block) > 1 for block in coarse),
    }
