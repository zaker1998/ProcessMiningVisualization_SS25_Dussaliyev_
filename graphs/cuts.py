from graphs.dfg import DFG
from collections import deque

"""
inspired by pseudocode in:

Leemans S.J.J., "Robust process mining with guarantees", Ph.D. Thesis, Eindhoven University of Technology,
"""


def exclusive_cut(graph: DFG) -> list[set[str | int], ...]:
    connected_components = graph.get_connected_components()
    return connected_components


def sequence_cut(graph: DFG) -> list[set[str | int], ...]:
    partitions = []

    current_partition = set(graph.get_start_nodes())
    next_partition = set()

    nodes_in_partition = set(graph.get_start_nodes())

    while nodes_in_partition != graph.get_nodes():
        queue = deque(current_partition)
        while queue:
            node = queue.popleft()
            successors = graph.get_successors(node)
            for successor in successors:
                if successor not in current_partition:
                    if is_successor_part_of_partition(
                        successor, current_partition, graph
                    ):
                        current_partition.add(successor)
                        nodes_in_partition.add(successor)
                        queue.append(successor)
                    else:
                        next_partition.add(successor)
                        nodes_in_partition.add(successor)

        partitions.append(current_partition)
        current_partition = next_partition
        next_partition = set()
        queue = deque(current_partition)

    partitions.append(current_partition)

    return partitions


def parallel_cut(graph: DFG) -> list[set[str | int], ...]:
    partitions = [{node} for node in graph.get_nodes()]


def loop_cut(graph: DFG) -> list[set[str | int], ...]:
    pass


def is_successor_part_of_partition(successor, partition, graph):
    for node in partition:
        if (
            graph.is_reachable(node, successor) and graph.is_reachable(successor, node)
        ) or (
            not graph.is_reachable(successor, node)
            and not graph.is_reachable(node, successor)
        ):
            return True

    return False
