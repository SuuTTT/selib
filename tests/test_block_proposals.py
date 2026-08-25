import networkx as nx

from selib.block_proposals import (
    agreement_blocks,
    deduplicate_blocks,
    induced_component_blocks,
)


def test_agreement_blocks_do_not_require_cross_view_label_alignment():
    first = [0, 0, 1, 1, 1, 0]
    second = [9, 9, 4, 4, 7, 7]
    assert agreement_blocks([first, second]) == [(0, 1), (2, 3)]


def test_induced_components_split_a_fragmented_predicted_community():
    graph = nx.Graph([(0, 1), (2, 3), (1, 4), (4, 5)])
    labels = [0, 0, 0, 0, 1, 1]
    assert induced_component_blocks(graph, labels) == [(0, 1), (2, 3), (4, 5)]


def test_deduplication_is_canonical():
    assert deduplicate_blocks([(2, 1), (1, 2), (4,), (), (3, 5)]) == [
        (1, 2), (3, 5), (4,)
    ]
