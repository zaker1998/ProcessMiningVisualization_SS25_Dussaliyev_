from graphs.dfg import DFG
from collections import deque


def exclusive_cut(graph: DFG) -> list[set[str | int], ...]:
    connected_components = graph.get_connected_components()
    return connected_components if len(connected_components) > 1 else None


def sequence_cut(graph: DFG) -> list[set[str | int], ...]:
    partitions = [{node} for node in graph.get_nodes()]
    nodes = list(graph.get_nodes())

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            node_1 = nodes[i]
            node_2 = nodes[j]
            is_j_reachable_from_i = graph.is_reachable(node_1, node_2)
            is_i_reachable_from_j = graph.is_reachable(node_2, node_1)

            # merge partitions if the nodes are reachable from each other or not reachable from each other
            if (is_j_reachable_from_i and is_i_reachable_from_j) or (
                not is_i_reachable_from_j and not is_j_reachable_from_i
            ):
                partition_1 = None
                partition_2 = None

                for partition in partitions:
                    if partition_1 and partition_2:
                        break

                    if node_1 in partition:
                        partition_1 = partition

                    if node_2 in partition:
                        partition_2 = partition

                if partition_1 != partition_2:
                    partition_1.update(partition_2)
                    partitions.remove(partition_2)

    # sort partitions by the order of reachability i < j if i is reachable from j
    for i in range(len(partitions)):
        min_partition_index = i
        for j in range(i + 1, len(partitions)):
            if graph.is_reachable(
                next(iter(partitions[j])), next(iter(partitions[min_partition_index]))
            ):
                min_partition_index = j

        partitions[i], partitions[min_partition_index] = (
            partitions[min_partition_index],
            partitions[i],
        )

    return partitions if len(partitions) > 1 else None


def parallel_cut(graph: DFG) -> list[set[str | int], ...]:
    inverted_dfg = create_inverted_dfg(graph)
    partitions = inverted_dfg.get_connected_components()

    if len(partitions) == 1:
        return None

    partitions_to_merge = [
        partition
        for partition in partitions
        if not partition.intersection(graph.get_start_nodes())
        or not partition.intersection(graph.get_end_nodes())
    ]

    partitions = [
        partition for partition in partitions if partition not in partitions_to_merge
    ]

    partitions_with_only_start_nodes = list()
    partitions_with_only_end_nodes = list()
    partitions_without_start_end_nodes = list()

    # split partitions into partitions with only start nodes, partitions with only end nodes and partitions without start and end nodes
    for partition in partitions_to_merge:
        has_start_node = len(partition.intersection(graph.get_start_nodes())) > 0
        has_end_node = len(partition.intersection(graph.get_end_nodes())) > 0

        if has_start_node:
            partitions_with_only_start_nodes.append(partition)

        elif has_end_node:
            partitions_with_only_end_nodes.append(partition)

        else:
            partitions_without_start_end_nodes.append(partition)

    partitions_to_merge = partitions_without_start_end_nodes

    # merge partitions with only start nodes with partitions with only end nodes
    for start_node_partition, end_node_partition in zip(
        partitions_with_only_start_nodes, partitions_with_only_end_nodes
    ):
        partitions.append(start_node_partition.union(end_node_partition))

    # if the number of partitions with only start nodes is not equal to the number of partitions with only end nodes
    # merge the remaining partitions with the other partitions to merge
    if len(partitions_with_only_end_nodes) != len(partitions_with_only_start_nodes):
        index = min(
            len(partitions_with_only_start_nodes), len(partitions_with_only_end_nodes)
        )

        if len(partitions_with_only_start_nodes) > len(partitions_with_only_end_nodes):
            partitions_to_merge.extend(partitions_with_only_start_nodes[index:])
        else:
            partitions_to_merge.extend(partitions_with_only_end_nodes[index:])

    # merge partitions without start and end nodes with partitions with start and end nodes
    index_to_merge = 0
    for partition in partitions_to_merge:
        partitions[index_to_merge] = partitions[index_to_merge].union(partition)
        index_to_merge = (index_to_merge + 1) % len(partitions)

    return partitions if len(partitions) > 1 else None


def loop_cut(graph: DFG) -> list[set[str | int], ...]:
    partition_1 = set(graph.get_start_nodes().union(graph.get_end_nodes()))

    starting_nodes = graph.get_start_nodes()
    ending_nodes = graph.get_end_nodes()

    dfg_without_end_start_nodes = create_dfg_without_nodes(
        graph, starting_nodes.union(ending_nodes)
    )

    # create partitions thath ar not connected to each other
    connected_components = dfg_without_end_start_nodes.get_connected_components()
    if len(connected_components) > 0:
        return None

    # check other conditions for partitions if not fullfiled merge with partition_1
    for partition in connected_components:
        pass
        # check if edges from partition to end node (that is not also a start node) exists if yes merge with partition one

        # check if edges from start nodes (that are not an end node) to partition exists if yes merge with partition one

    # check for all connected components the following conditions
    # 1. if there is an edge from an end node to a node in the connected component there have to be edges from all end nodes to this node
    # 2. if there is an edge from a node in the connected component to a start node there have to be edges from this node to all start nodes
    # if one of the conditions is not fullfiled merge the connected component with partition_1

    partitions = [partition_1, *connected_components]
    return partitions if len(partitions) > 1 else None


def create_dfg_without_nodes(graph: DFG, nodes: set[str | int]) -> DFG:
    dfg_without_nodes = DFG()

    for edge in graph.get_edges():
        source, destination = edge
        if source not in nodes and destination not in nodes:
            dfg_without_nodes.add_edge(source, destination)

    return dfg_without_nodes


def create_inverted_dfg(graph: DFG) -> DFG:
    inverted_dfg = DFG()

    edges = graph.get_edges()
    nodes = list(graph.get_nodes())

    for node in nodes:
        inverted_dfg.add_node(node)

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            node_1 = nodes[i]
            node_2 = nodes[j]

            if not graph.contains_edge(node_1, node_2) or not graph.contains_edge(
                node_2, node_1
            ):
                inverted_dfg.add_edge(node_1, node_2)
                inverted_dfg.add_edge(node_2, node_1)

    return inverted_dfg
