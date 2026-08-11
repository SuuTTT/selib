import random

import networkx as nx

from selib.htree import (
    TNode,
    _do_graft,
    _do_nni,
    _graft_candidates,
    _graph_arrays,
    _nni_candidates,
    annotate,
    hd_se,
    nni_delta,
    random_coalescent_tree,
    refine_graft,
    refine_nni,
    refine_nni_compound,
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


def test_two_step_nni_escapes_a_strict_one_move_local_optimum():
    """Regression witness found by scripts/find_nni_trap.py (seed 1)."""
    seed = 1
    rng = random.Random(seed)
    n = 8
    graph = nx.gnp_random_graph(n, 0.38, seed=seed)
    for node in range(n - 1):
        graph.add_edge(node, node + 1)
    for u, v in graph.edges():
        graph[u][v]["weight"] = round(0.2 + 2.8 * rng.random(), 6)

    forest = [TNode(vertex=i) for i in range(n)]
    while len(forest) > 1:
        first, second = sorted(rng.sample(range(len(forest)), 2), reverse=True)
        left = forest.pop(first)
        right = forest.pop(second)
        forest.append(TNode(children=[left, right]))
    root = forest[0]

    _, _, _, adj, deg, vol = _graph_arrays(graph)
    local = refine_nni(root, deg, adj, vol)
    annotate(local, deg, adj, vol)
    local_h = hd_se(local, vol)
    for child_path, promoted_child in _nni_candidates(local):
        assert nni_delta(local, child_path, promoted_child, adj, vol) >= -1e-10

    escaped, trace = refine_nni_compound(
        local, deg, adj, vol,
        max_rounds=2,
        beam_width=32,
        barrier_bits=0.25,
        return_trace=True,
    )
    annotate(escaped, deg, adj, vol)
    escaped_h = hd_se(escaped, vol)
    compound = [step for step in trace if step["kind"] == "compound"]

    assert compound
    assert compound[0]["barrier"] > 0.0
    assert escaped_h < local_h - 0.04


def test_fast_multi_start_nni_is_no_worse_than_its_agglomerative_start():
    from selib.calc import optimal_tree_nni_fast
    from selib.se import se_agglomerative
    from selib.htree import linkage_to_tree

    graph = _random_weighted_graph(18, 44)
    _, _, n, adj, deg, vol = _graph_arrays(graph)
    baseline = linkage_to_tree(se_agglomerative(graph), n)
    annotate(baseline, deg, adj, vol)
    baseline_h = hd_se(baseline, vol)

    _, fast_h = optimal_tree_nni_fast(graph, seed=44)
    assert fast_h <= baseline_h + 1e-10


def test_random_restart_mode_is_deterministic_and_never_worsens_candidate_pool():
    from selib.htree import encoding_tree_nni_fast

    graph = _random_weighted_graph(10, 73)
    base_root, _, _, volume = encoding_tree_nni_fast(graph, seed=73)
    base_entropy = hd_se(base_root, volume)

    first, _, _, volume = encoding_tree_nni_fast(
        graph, seed=73, random_restarts=4, restart_seed=991
    )
    second, _, _, second_volume = encoding_tree_nni_fast(
        graph, seed=73, random_restarts=4, restart_seed=991
    )
    first_entropy = hd_se(first, volume)
    second_entropy = hd_se(second, second_volume)

    assert first_entropy <= base_entropy + 1e-10
    assert abs(first_entropy - second_entropy) < 1e-12


def test_random_coalescent_tree_contains_each_leaf_once():
    root = random_coalescent_tree(17, random.Random(5))
    leaves = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.is_leaf():
            leaves.append(node.vertex)
        else:
            assert len(node.children) == 2
            stack.extend(node.children)
    assert sorted(leaves) == list(range(17))


def _tree_signature(root):
    if root.is_leaf():
        return root.vertex
    return tuple(_tree_signature(child) for child in root.children)


def test_graft_preserves_binary_topology_and_leaf_set():
    root = TNode(children=[
        TNode(children=[TNode(vertex=0), TNode(vertex=1)]),
        TNode(children=[
            TNode(children=[TNode(vertex=2), TNode(vertex=3)]),
            TNode(vertex=4),
        ]),
    ])
    candidates = _graft_candidates(root)
    assert candidates

    grafted = _do_graft(root, (0, 0), (1, 0, 1))
    assert grafted is not None
    assert _tree_signature(root) == ((0, 1), ((2, 3), 4))

    leaves = []
    stack = [grafted]
    while stack:
        node = stack.pop()
        if node.is_leaf():
            leaves.append(node.vertex)
        else:
            assert len(node.children) == 2
            stack.extend(node.children)
    assert sorted(leaves) == [0, 1, 2, 3, 4]


def test_full_rescore_graft_refinement_is_monotone_and_graft_local():
    graph = _random_weighted_graph(9, 311)
    root = _random_binary_tree(9, 912)
    _, _, _, adj, deg, vol = _graph_arrays(graph)
    annotate(root, deg, adj, vol)
    before = hd_se(root, vol)

    refined, trace = refine_graft(
        root, deg, adj, vol, max_rounds=100, post_nni=True, return_trace=True
    )
    annotate(refined, deg, adj, vol)
    after = hd_se(refined, vol)
    assert after <= before + 1e-10
    assert all(
        step["after"] < step["before"]
        for step in trace
        if step["kind"] == "graft"
    )

    for source_path, target_path in _graft_candidates(refined):
        candidate = _do_graft(refined, source_path, target_path)
        assert candidate is not None
        annotate(candidate, deg, adj, vol)
        assert hd_se(candidate, vol) >= after - 1e-10
