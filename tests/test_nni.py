import random

import networkx as nx

from selib.htree import (
    TNode,
    _do_nni,
    _graph_arrays,
    _nni_candidates,
    annotate,
    hd_se,
    nni_delta,
    refine_nni,
)


def _random_binary_tree(n, seed):
    rng = random.Random(seed)
    forest = [TNode(vertex=i) for i in range(n)]
    while len(forest) > 1:
        left, right = rng.sample(range(len(forest)), 2)
        if left < right:
            right_node = forest.pop(right)
            left_node = forest.pop(left)
        else:
            left_node = forest.pop(left)
            right_node = forest.pop(right)
        forest.append(TNode(children=[left_node, right_node]))
    return forest[0]


def _random_weighted_graph(n, seed):
    rng = random.Random(seed)
    graph = nx.gnp_random_graph(n, 0.45, seed=seed)
    # Ensure nonzero volume and a connected backbone without changing labels.
    for node in range(n - 1):
        graph.add_edge(node, node + 1)
    for u, v in graph.edges():
        graph[u][v]["weight"] = 0.1 + 2.0 * rng.random()
    return graph


def test_weighted_nni_delta_matches_full_entropy_recomputation():
    checked = 0
    for seed in range(12):
        n = 5 + seed % 5
        graph = _random_weighted_graph(n, seed)
        root = _random_binary_tree(n, seed + 100)
        _, _, _, adj, deg, vol = _graph_arrays(graph)
        annotate(root, deg, adj, vol)
        before = hd_se(root, vol)
        for child_path, promoted_child in _nni_candidates(root):
            predicted = nni_delta(
                root, child_path, promoted_child, adj, vol
            )
            candidate = _do_nni(root, child_path, promoted_child)
            assert candidate is not None
            annotate(candidate, deg, adj, vol)
            observed = hd_se(candidate, vol) - before
            assert abs(predicted - observed) < 1e-9
            checked += 1
    assert checked >= 100


def test_nni_refinement_is_monotone_and_one_move_local():
    graph = _random_weighted_graph(12, 7)
    root = _random_binary_tree(12, 91)
    _, _, _, adj, deg, vol = _graph_arrays(graph)
    annotate(root, deg, adj, vol)
    before = hd_se(root, vol)

    refined, trace = refine_nni(
        root, deg, adj, vol, return_trace=True
    )
    annotate(refined, deg, adj, vol)
    after = hd_se(refined, vol)

    assert after <= before + 1e-10
    assert all(step["after"] < step["before"] for step in trace)
    for child_path, promoted_child in _nni_candidates(refined):
        delta = nni_delta(
            refined, child_path, promoted_child, adj, vol
        )
        assert delta >= -1e-10


def test_se_hier_nni_cannot_worsen_se_hier_objective():
    from selib.calc import optimal_tree, optimal_tree_nni

    graph = nx.karate_club_graph()
    _, baseline = optimal_tree(graph, seed=3)
    _, refined = optimal_tree_nni(graph, seed=3)
    assert refined <= baseline + 1e-10
