import networkx as nx

from selib.seopt import _State, _from_graph, _spectral_seed_labels


def _state(graph, labels):
    n, adjacency, degree, loops, volume, _, _ = _from_graph(graph)
    return _State(n, adjacency, degree, loops, volume, list(labels))


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
    state.apply(0, 1, state._w_to(0))
    assert state.size[0] == 1
    assert state.V[0] == 0.0
    assert set(state.comm) == set(state.V) == {0, 1}
