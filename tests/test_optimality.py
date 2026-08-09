import networkx as nx

from selib.htree import TNode, _graph_arrays, annotate, hd_se
from selib.optimality import edge_lca_lower_bound, exact_tree_entropy


def _all_binary_trees(vertices):
    vertices = tuple(sorted(vertices))
    if len(vertices) == 1:
        yield TNode(vertex=vertices[0])
        return
    anchor = vertices[0]
    others = vertices[1:]
    for mask in range(1 << len(others)):
        left = (anchor,) + tuple(
            vertex for index, vertex in enumerate(others) if mask & (1 << index)
        )
        right = tuple(vertex for vertex in vertices if vertex not in left)
        if not right:
            continue
        for left_tree in _all_binary_trees(left):
            for right_tree in _all_binary_trees(right):
                yield TNode(children=[left_tree, right_tree])


def test_exact_dp_rebuilds_its_optimal_tree():
    graph = nx.Graph()
    graph.add_weighted_edges_from([
        (0, 1, 2.0), (1, 2, 0.7), (2, 3, 1.8), (0, 3, 0.2),
    ])
    optimum, tree = exact_tree_entropy(graph, return_tree=True)
    _, _, _, adjacency, degree, volume = _graph_arrays(graph)
    annotate(tree, degree, adjacency, volume)
    assert abs(hd_se(tree, volume) - optimum) < 1e-10
    assert edge_lca_lower_bound(graph) <= optimum + 1e-10


def test_exact_dp_dominates_a_hand_built_tree():
    graph = nx.path_graph(5)
    tree = TNode(children=[
        TNode(children=[TNode(vertex=0), TNode(vertex=4)]),
        TNode(children=[
            TNode(vertex=1),
            TNode(children=[TNode(vertex=2), TNode(vertex=3)]),
        ]),
    ])
    _, _, _, adjacency, degree, volume = _graph_arrays(graph)
    annotate(tree, degree, adjacency, volume)
    assert exact_tree_entropy(graph) <= hd_se(tree, volume) + 1e-10


def test_exact_dp_matches_independent_tree_enumeration():
    graph = nx.Graph()
    graph.add_weighted_edges_from([
        (0, 1, 1.8), (0, 2, 0.3), (1, 3, 0.7),
        (2, 3, 1.4), (2, 4, 0.9), (3, 4, 1.2),
    ])
    _, _, _, adjacency, degree, volume = _graph_arrays(graph)
    brute = float("inf")
    count = 0
    for tree in _all_binary_trees(range(5)):
        annotate(tree, degree, adjacency, volume)
        brute = min(brute, hd_se(tree, volume))
        count += 1
    assert count == 105
    assert abs(exact_tree_entropy(graph) - brute) < 1e-10


def test_binary_refinement_cannot_worsen_a_multiway_root():
    graph = nx.cycle_graph(4)
    multiway = TNode(children=[TNode(vertex=i) for i in range(4)])
    refined = TNode(children=[
        TNode(children=[TNode(vertex=0), TNode(vertex=1)]),
        TNode(vertex=2),
        TNode(vertex=3),
    ])
    _, _, _, adjacency, degree, volume = _graph_arrays(graph)
    annotate(multiway, degree, adjacency, volume)
    annotate(refined, degree, adjacency, volume)
    assert hd_se(refined, volume) <= hd_se(multiway, volume) + 1e-10
