from graphs.dfg import DFG
from collections import deque

"""
parts inspired by pseudocode in:
Leemans S.J.J., "Robust process mining with guarantees", Ph.D. Thesis, Eindhoven University of Technology

and by:
Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P. (2013). Discovering Block-Structured Process Models from Event Logs - 
A Constructive Approach. In: Colom, JM., Desel, J. (eds) Application and Theory of Petri Nets and Concurrency. PETRI NETS 2013. 
Lecture Notes in Computer Science, vol 7927. Springer, Berlin, Heidelberg (pp. 311-329)
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
    nodes = list(graph.get_nodes())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            node_1 = nodes[i]
            node_2 = nodes[j]

            if not graph.contains_edge(node_1, node_2) or not graph.contains_edge(
                node_2, node_1
            ):
                # merge partitions
                partition_node_1 = list(filter(lambda x: node_1 in x, partitions))[0]
                partition_node_2 = list(filter(lambda x: node_2 in x, partitions))[0]

                # print(partition_node_1, partition_node_2)

                if partition_node_1 != partition_node_2:
                    partition_node_1.update(partition_node_2)
                    partitions.remove(partition_node_2)

    # check if each partition has at least one start node and one end node
    # if not, merge partition with another partition that has a start node and an end node
    maximum_number_of_valid_partitions = min(
        len(graph.get_start_nodes()), len(graph.get_end_nodes())
    )
    if len(partitions) > maximum_number_of_valid_partitions:
        print("Merging partitions required")

    return partitions


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
