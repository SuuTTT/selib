import math

from selib.basin import (
    coalescent_history_count,
    coalescent_history_total,
    planted_recovery,
    rooted_binary_topologies,
    topology_to_tree,
)


def test_rooted_binary_topology_counts_and_coalescent_mass():
    expected = {1: 1, 2: 1, 3: 3, 4: 15, 5: 105, 6: 945, 7: 10395}
    for n, count in expected.items():
        topologies = rooted_binary_topologies(n)
        assert len(topologies) == count
        assert len(set(topologies)) == count
        assert sum(map(coalescent_history_count, topologies)) == (
            coalescent_history_total(n)
        )


def test_coalescent_weights_are_not_uniform_from_four_leaves():
    topologies = rooted_binary_topologies(4)
    weights = [
        coalescent_history_count(topology) / coalescent_history_total(4)
        for topology in topologies
    ]
    assert math.isclose(sum(weights), 1.0)
    assert len(set(weights)) > 1


def test_strict_planted_recovery_requires_both_levels():
    topology = (((0, 1), (2, 3)), ((4, 5), (6, 7)))
    recovered = planted_recovery(
        topology_to_tree(topology),
        fine_blocks=[[0, 1], [2, 3], [4, 5], [6, 7]],
        coarse_blocks=[[0, 1, 2, 3], [4, 5, 6, 7]],
    )
    assert recovered["strict_recovered"]

    missed = planted_recovery(
        topology_to_tree(topology),
        fine_blocks=[[0, 2], [1, 3], [4, 5], [6, 7]],
        coarse_blocks=[[0, 1, 2, 3], [4, 5, 6, 7]],
    )
    assert missed["coarse_recovered"]
    assert not missed["fine_recovered"]
    assert not missed["strict_recovered"]
