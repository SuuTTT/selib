import random

import networkx as nx

from selib.blockopt import (
    apply_block_move,
    exact_block_move,
    refine_blocks_fixed_k,
    refine_pairwise_merge_split_fixed_k,
    se_optimize_block_fixed_k,
)
from selib.metrics import structural_entropy_2d
from selib.seopt import _State, _from_graph, _spectral_seed_labels


def _state(graph, labels):
    n, adjacency, degree, loops, volume, _, _ = _from_graph(graph)
    return _State(n, adjacency, degree, loops, volume, list(labels))


def test_exact_block_delta_matches_full_recomputation_with_weights_and_loops():
    rng = random.Random(9)
    graph = nx.Graph()
    graph.add_nodes_from(range(12))
    for vertex in graph:
        if rng.random() < 0.3:
            graph.add_edge(vertex, vertex, weight=rng.random() + 0.1)
    for left in graph:
        for right in range(left + 1, 12):
            if rng.random() < 0.35:
                graph.add_edge(left, right, weight=rng.random() * 2.0 + 0.1)
    labels = [vertex % 3 for vertex in graph]
    state = _state(graph, labels)
    block = (0, 3)
    move = exact_block_move(state, block, target=1)
    before = state.obj
    apply_block_move(state, move)
    rebuilt = _state(graph, state.comm)
    assert abs(state.obj - rebuilt.obj) < 1e-12
    assert abs((state.obj - before) - move.delta) < 1e-12
    assert len(set(state.comm)) == 3


def test_block_refinement_is_monotone_and_preserves_exact_k():
    graph = nx.Graph()
    graph.add_weighted_edges_from([
        (0, 1, 5.0), (1, 2, 5.0), (0, 2, 5.0),
        (3, 4, 5.0), (4, 5, 5.0), (3, 5, 5.0),
        (2, 3, 0.1),
    ])
    # The first dense triangle is fragmented: vertices 1 and 2 must move
    # together because moving either one alone cuts their strong mutual edge.
    initial = [0, 1, 1, 1, 1, 1]
    refined, audit = refine_blocks_fixed_k(graph, initial, blocks=[(1, 2)])
    assert len(set(refined)) == len(set(initial)) == 2
    assert audit["accepted_moves"]
    assert audit["certified_block_local"]
    assert all(
        after < before - 1e-12
        for before, after in zip(audit["objective_path"], audit["objective_path"][1:])
    )
    assert structural_entropy_2d(graph, refined) < structural_entropy_2d(graph, initial)


def test_sparse_spectral_seed_runs_above_previous_3000_vertex_cliff():
    graph = nx.disjoint_union(nx.path_graph(1501), nx.path_graph(1501))
    labels = _spectral_seed_labels(graph, 2, seed=4)
    assert len(labels) == 3002
    assert len(set(labels)) == 2


def test_fixed_k_state_keeps_a_nonempty_zero_volume_community():
    graph = nx.Graph()
    graph.add_nodes_from(range(4))
    graph.add_edge(0, 2, weight=1.0)
    state = _state(graph, [0, 0, 1, 1])
    weights = state._w_to(0)
    state.apply(0, 1, weights)
    assert state.size[0] == 1
    assert state.V[0] == 0.0
    assert set(state.comm) == set(state.V) == {0, 1}


def test_joint_optimizer_escapes_a_certified_node_local_partition():
    graph = nx.Graph()
    graph.add_weighted_edges_from([
        (0, 7, 5.884478), (1, 3, 4.273878), (1, 7, 1.652950),
        (2, 7, 2.453459), (2, 9, 2.831509), (3, 7, 0.636898),
        (3, 8, 0.932882), (4, 5, 5.962237), (4, 8, 4.777694),
        (5, 7, 4.413439), (6, 7, 1.128564), (6, 9, 2.493888),
        (7, 9, 4.927047),
    ])
    node_local = [1, 1, 1, 1, 0, 0, 1, 1, 0, 1]
    labels, audit = se_optimize_block_fixed_k(
        graph,
        2,
        blocks=[(1, 3)],
        initial_partitions=[node_local],
        starts=1,
        seed=20260825,
        return_audit=True,
    )
    assert len(set(labels)) == 2
    assert structural_entropy_2d(graph, labels) < structural_entropy_2d(graph, node_local)
    assert audit["selection_criterion"] == "exact_2d_structural_entropy"


def test_joint_optimizer_handles_the_single_community_case():
    graph = nx.path_graph(5)
    labels, audit = se_optimize_block_fixed_k(
        graph, 1, blocks=[], starts=8, return_audit=True
    )
    assert labels == [0] * 5
    assert audit["restart_count"] == 1


def test_pairwise_merge_split_is_exact_k_and_nonincreasing():
    graph = nx.karate_club_graph()
    initial = [vertex % 3 for vertex in graph]
    labels, audit = refine_pairwise_merge_split_fixed_k(
        graph, initial, max_passes=2, pair_node_passes=10, seed=3
    )
    assert len(set(labels)) == len(set(initial)) == 3
    assert structural_entropy_2d(graph, labels) <= structural_entropy_2d(graph, initial) + 1e-12
    assert all(move["delta"] < -1e-12 for move in audit["accepted_moves"])
