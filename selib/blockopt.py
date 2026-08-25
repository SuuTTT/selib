"""Exact fixed-K block moves for two-dimensional structural entropy.

The node-local search in :mod:`selib.seopt` can be trapped when a useful move
requires relocating several vertices together.  This module scores and applies
such proposals without approximating the structural-entropy objective.  It is
deliberately proposal-agnostic: callers may supply topology components,
attribute-agreement blocks, or matched random controls, while the optimizer
selects proposals solely by exact objective decrease.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Iterable, Sequence

from .seopt import (
    _State,
    _from_graph,
    _local_moves_fixed_k,
    _relabel,
    _spectral_seed_labels,
    _term,
)


@dataclass(frozen=True)
class BlockMove:
    """A fully specified move and its exact change in the partition term."""

    block: tuple[int, ...]
    source: int
    target: int
    delta: float
    volume: float
    boundary: float
    weight_to_source: float
    weight_to_target: float


def _normalise_block(block: Iterable[int], n: int) -> tuple[int, ...]:
    vertices = tuple(sorted(set(int(v) for v in block)))
    if not vertices:
        raise ValueError("block must be non-empty")
    if vertices[0] < 0 or vertices[-1] >= n:
        raise ValueError("block contains an out-of-range vertex")
    return vertices


def _block_statistics(state: _State, vertices: Sequence[int], source: int, target: int):
    """Return ``(volume, boundary, w_source, w_target)`` for a proposal.

    ``boundary`` is the total edge weight from the block to its complement.
    Self-loops and internal non-loop edges therefore contribute twice to block
    volume and zero to its boundary, matching NetworkX weighted-degree rules.
    """
    chosen = set(vertices)
    volume = sum(state.deg[v] for v in vertices)
    internal = sum(state.sl[v] for v in vertices)
    weight_to_source = 0.0
    weight_to_target = 0.0
    for v in vertices:
        for u, weight in state.adj[v].items():
            if u in chosen:
                if v < u:
                    internal += weight
            elif state.comm[u] == source:
                weight_to_source += weight
            elif state.comm[u] == target:
                weight_to_target += weight
    boundary = volume - 2.0 * internal
    # Floating arithmetic can produce a tiny negative residue.
    if boundary < 0.0 and boundary > -1e-12:
        boundary = 0.0
    return volume, boundary, weight_to_source, weight_to_target


def exact_block_move(state: _State, block: Iterable[int], target: int) -> BlockMove:
    """Score moving ``block`` to an existing community exactly.

    Every block vertex must currently belong to the same source community.  The
    move is rejected if it would empty that source, which preserves exactly K
    non-empty communities.
    """
    vertices = _normalise_block(block, state.n)
    source = state.comm[vertices[0]]
    if any(state.comm[v] != source for v in vertices):
        raise ValueError("all block vertices must share one source community")
    if target == source or target not in state.V:
        raise ValueError("target must be a different existing community")
    source_size = state.size[source]
    if len(vertices) >= source_size:
        raise ValueError("move would empty the source community")

    volume, boundary, w_source, w_target = _block_statistics(
        state, vertices, source, target
    )
    source_volume, source_cut = state.V[source], state.g.get(source, 0.0)
    target_volume, target_cut = state.V[target], state.g.get(target, 0.0)
    new_source_volume = source_volume - volume
    new_target_volume = target_volume + volume
    new_source_cut = source_cut - boundary + 2.0 * w_source
    new_target_cut = target_cut + boundary - 2.0 * w_target
    delta = (
        _term(new_source_volume, new_source_cut, state.two_m)
        + _term(new_target_volume, new_target_cut, state.two_m)
        - _term(source_volume, source_cut, state.two_m)
        - _term(target_volume, target_cut, state.two_m)
    )
    return BlockMove(
        block=vertices,
        source=source,
        target=target,
        delta=delta,
        volume=volume,
        boundary=boundary,
        weight_to_source=w_source,
        weight_to_target=w_target,
    )


def apply_block_move(state: _State, move: BlockMove) -> None:
    """Apply a previously scored move in time linear in its block boundary."""
    # Fail closed if an intervening move invalidated this proposal.
    checked = exact_block_move(state, move.block, move.target)
    if checked.source != move.source or abs(checked.delta - move.delta) > 1e-10:
        raise ValueError("stale block move")

    source, target = move.source, move.target
    old_source = _term(state.V[source], state.g.get(source, 0.0), state.two_m)
    old_target = _term(state.V[target], state.g.get(target, 0.0), state.two_m)
    state.V[source] -= move.volume
    state.V[target] += move.volume
    state.g[source] = state.g.get(source, 0.0) - move.boundary + 2.0 * move.weight_to_source
    state.g[target] = state.g.get(target, 0.0) + move.boundary - 2.0 * move.weight_to_target
    for vertex in move.block:
        state.comm[vertex] = target
    state.size[source] -= len(move.block)
    state.size[target] += len(move.block)
    new_source = _term(state.V[source], state.g[source], state.two_m)
    new_target = _term(state.V[target], state.g[target], state.two_m)
    state.obj += new_source + new_target - old_source - old_target


def refine_blocks_fixed_k(
    G,
    labels: Sequence[int],
    blocks: Iterable[Iterable[int]],
    *,
    max_passes: int = 20,
    tolerance: float = 1e-12,
):
    """Monotonically refine an exactly-K partition with supplied block proposals.

    Vertex ids in ``blocks`` are integer positions aligned with ``list(G.nodes())``.
    Each pass evaluates every still-valid block against every existing target and
    applies its best strict improvement.  The return value is ``(labels, audit)``;
    the audit records the objective path and accepted exact deltas.
    """
    n, adj, deg, sl, two_m, _, _ = _from_graph(G)
    if len(labels) != n:
        raise ValueError("labels must align with list(G.nodes())")
    initial = _relabel([int(c) for c in labels])
    state = _State(n, adj, deg, sl, two_m, initial)
    proposals = tuple(_normalise_block(block, n) for block in blocks)
    objective_path = [state.obj]
    accepted = []
    certified = False

    for pass_index in range(max_passes):
        moved = False
        for block_index, block in enumerate(proposals):
            sources = {state.comm[v] for v in block}
            if len(sources) != 1:
                continue
            source = next(iter(sources))
            if len(block) >= state.size[source]:
                continue
            best = None
            for target in sorted(state.V):
                if target == source:
                    continue
                move = exact_block_move(state, block, target)
                if best is None or move.delta < best.delta - tolerance:
                    best = move
            if best is not None and best.delta < -tolerance:
                before = state.obj
                apply_block_move(state, best)
                accepted.append({
                    "pass": pass_index,
                    "proposal": block_index,
                    "source": best.source,
                    "target": best.target,
                    "size": len(best.block),
                    "delta": best.delta,
                })
                objective_path.append(state.obj)
                if state.obj >= before - tolerance:
                    raise ArithmeticError("accepted block move was not a strict decrease")
                moved = True
        if not moved:
            certified = True
            break

    return _relabel(state.comm), {
        "initial_objective_term": objective_path[0],
        "final_objective_term": objective_path[-1],
        "objective_path": objective_path,
        "accepted_moves": accepted,
        "passes": (accepted[-1]["pass"] + 1) if accepted else 0,
        "certified_block_local": certified,
        "proposal_count": len(proposals),
    }


def fixed_k_node_certificate(state: _State, *, tolerance: float = 1e-12):
    """Certify that no legal singleton move decreases the exact objective."""
    best_delta = 0.0
    best_move = None
    for vertex in range(state.n):
        source = state.comm[vertex]
        if state.size[source] <= 1:
            continue
        for target in sorted(state.V):
            if target == source:
                continue
            move = exact_block_move(state, (vertex,), target)
            if move.delta < best_delta:
                best_delta = move.delta
                best_move = move
    return {
        "certified_node_local": best_delta >= -tolerance,
        "best_legal_node_delta": best_delta,
        "best_vertex": best_move.block[0] if best_move else None,
        "best_target": best_move.target if best_move else None,
    }


def _refine_pair(state, vertices, left, right, max_passes, tolerance):
    """Exact singleton refinement restricted to a two-community union."""
    for _ in range(max_passes):
        moved = False
        for vertex in vertices:
            source = state.comm[vertex]
            if source not in (left, right) or state.size[source] <= 1:
                continue
            target = right if source == left else left
            move = exact_block_move(state, (vertex,), target)
            if move.delta < -tolerance:
                apply_block_move(state, move)
                moved = True
        if not moved:
            break


def refine_pairwise_merge_split_fixed_k(
    G,
    labels: Sequence[int],
    *,
    split_graphs: Iterable = (),
    max_passes: int = 3,
    pair_node_passes: int = 20,
    tolerance: float = 1e-12,
    seed: int = 0,
):
    """Exact-objective pairwise merge-split refinement.

    For each pair of current communities, temporarily merge their vertices and
    bipartition the union using sparse spectral proposals from ``G`` and any
    supplied label-free views.  Singleton moves then refine only that union.
    The globally best candidate is accepted iff its exact objective decreases.
    Community count is unchanged throughout.
    """
    n, adj, deg, sl, two_m, _, nodes = _from_graph(G)
    if len(labels) != n:
        raise ValueError("labels must align with list(G.nodes())")
    state = _State(n, adj, deg, sl, two_m, _relabel([int(c) for c in labels]))
    views = [G]
    for view in split_graphs:
        if set(view.nodes()) != set(nodes):
            raise ValueError("every split graph must contain the same nodes as G")
        if view is not G:
            views.append(view)
    accepted = []
    certified = False

    for pass_index in range(max_passes):
        best_state = None
        best_meta = None
        communities = sorted(state.V)
        for pair_index, (left, right) in enumerate(itertools.combinations(communities, 2)):
            vertices = [
                vertex for vertex, community in enumerate(state.comm)
                if community in (left, right)
            ]
            union_nodes = [nodes[vertex] for vertex in vertices]
            for view_index, view in enumerate(views):
                subgraph = view.subgraph(union_nodes).copy()
                binary = _spectral_seed_labels(
                    subgraph,
                    2,
                    seed=seed + pass_index * 1_000_003 + pair_index * 997 + view_index,
                )
                by_node = dict(zip(subgraph.nodes(), binary))
                candidate = state.comm[:]
                for vertex in vertices:
                    candidate[vertex] = left if by_node[nodes[vertex]] == 0 else right
                candidate_state = _State(n, adj, deg, sl, two_m, candidate)
                _refine_pair(
                    candidate_state,
                    vertices,
                    left,
                    right,
                    pair_node_passes,
                    tolerance,
                )
                delta = candidate_state.obj - state.obj
                if best_state is None or delta < best_meta["delta"] - tolerance:
                    best_state = candidate_state
                    best_meta = {
                        "pass": pass_index,
                        "left": left,
                        "right": right,
                        "view": view_index,
                        "union_size": len(vertices),
                        "delta": delta,
                    }
        if best_state is None or best_meta["delta"] >= -tolerance:
            certified = True
            break
        state = best_state
        accepted.append(best_meta)

    return _relabel(state.comm), {
        "schema": "selib.pairwise_merge_split_audit.v1",
        "accepted_moves": accepted,
        "certified_pairwise_local": certified,
        "final_objective_term": state.obj,
        "view_count": len(views),
    }


def se_optimize_block_fixed_k(
    G,
    k: int,
    blocks: Iterable[Iterable[int]],
    *,
    initial_partitions: Iterable[Sequence[int]] = (),
    starts: int = 8,
    max_node_passes: int = 30,
    max_block_passes: int = 20,
    max_outer_cycles: int = 10,
    tolerance: float = 1e-12,
    seed: int = 0,
    return_audit: bool = False,
):
    """Multi-start fixed-K node/block coordinate descent on exact 2D-SE.

    External initial partitions can encode topology, feature, or fused views.
    They are treated only as proposals: every restart and every accepted move is
    selected by the same exact objective on ``G``.  No labels or task metric are
    accepted by this API.
    """
    import random
    import numpy as np

    n, adj, deg, sl, two_m, _, _ = _from_graph(G)
    if k < 1 or k > n:
        raise ValueError("k out of range")
    proposals = tuple(_normalise_block(block, n) for block in blocks)
    inits = []
    seen_inits = set()

    def add_init(partition):
        labels = _relabel([int(c) for c in partition])
        if len(labels) != n or len(set(labels)) != k:
            raise ValueError("each initial partition must contain exactly k communities")
        key = tuple(labels)
        if key not in seen_inits:
            seen_inits.add(key)
            inits.append(labels)

    for partition in initial_partitions:
        add_init(partition)
    if k == 1:
        add_init([0] * n)
    else:
        add_init(_spectral_seed_labels(G, k, seed=seed))

    nrng = np.random.default_rng(seed)
    desired_starts = 1 if k == 1 else max(starts, 1)
    attempts = 0
    while len(inits) < desired_starts and attempts < desired_starts * 100:
        attempts += 1
        labels = [int(value) for value in nrng.integers(0, k, size=n)]
        for community, vertex in enumerate(nrng.permutation(n)[:k]):
            labels[int(vertex)] = community
        add_init(labels)

    best_labels = None
    best_objective = float("inf")
    best_index = None
    runs = []
    for restart, labels in enumerate(inits):
        state = _State(n, adj, deg, sl, two_m, labels)
        initial_objective = state.obj
        cycle_records = []
        for cycle in range(max_outer_cycles):
            before = state.obj
            _local_moves_fixed_k(
                state,
                random.Random(seed * 1_000_003 + restart * 997 + cycle),
                max_node_passes,
            )
            after_nodes = state.obj
            refined, block_audit = refine_blocks_fixed_k(
                G,
                state.comm,
                proposals,
                max_passes=max_block_passes,
                tolerance=tolerance,
            )
            state = _State(n, adj, deg, sl, two_m, refined)
            cycle_records.append({
                "cycle": cycle,
                "before": before,
                "after_nodes": after_nodes,
                "after_blocks": state.obj,
                "accepted_block_moves": len(block_audit["accepted_moves"]),
                "block_certificate": block_audit["certified_block_local"],
            })
            if state.obj >= before - tolerance:
                break

        node_certificate = fixed_k_node_certificate(state, tolerance=tolerance)
        # A final no-move block scan is necessary because the last accepted
        # singleton move could expose a new block improvement.
        final_labels, final_block_audit = refine_blocks_fixed_k(
            G,
            state.comm,
            proposals,
            max_passes=max_block_passes,
            tolerance=tolerance,
        )
        state = _State(n, adj, deg, sl, two_m, final_labels)
        certified = (
            node_certificate["certified_node_local"]
            and final_block_audit["certified_block_local"]
            and not final_block_audit["accepted_moves"]
        )
        runs.append({
            "restart": restart,
            "initial_objective_term": initial_objective,
            "final_objective_term": state.obj,
            "cycles": cycle_records,
            "node_certificate": node_certificate,
            "final_block_scan": final_block_audit,
            "joint_certificate": certified,
        })
        if state.obj < best_objective - tolerance:
            best_labels = state.comm[:]
            best_objective = state.obj
            best_index = restart

    labels = _relabel(best_labels)
    audit = {
        "schema": "selib.block_nest_k_audit.v1",
        "k": k,
        "seed": seed,
        "restart_count": len(inits),
        "proposal_count": len(proposals),
        "selection_criterion": "exact_2d_structural_entropy",
        "best_restart": best_index,
        "best_objective_term": best_objective,
        "best_joint_certificate": runs[best_index]["joint_certificate"],
        "runs": runs,
    }
    return (labels, audit) if return_audit else labels
