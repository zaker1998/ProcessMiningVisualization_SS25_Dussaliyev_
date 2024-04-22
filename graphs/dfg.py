from collections import deque
from utils.transformations import cases_list_to_dict


class DFG:
    """Implementation of a Directly Follows Graph (DFG)"""

    def __init__(self, log: list[list[str]] = None) -> None:
        self.start_nodes: set[str | int] = set()
        self.end_nodes: set[str | int] = set()
        self.successor_list: dict[str | int, set[str | int]] = dict()
        self.predecessor_list: dict[str | int, set[str | int]] = dict()
        # self.nodes: set[str | int] = set()
        # self.edges: dict[tuple[str | int, str | int], int] = dict()
        if log:
            self.__build_graph_from_log(log)

    def __build_graph_from_log(
        self, log: list[list[str]] | dict[tuple[str, ...], int]
    ) -> None:
        _log = log
        if isinstance(log, list):
            _log = cases_list_to_dict(log)

        for trace, frequency in _log.items():
            if len(trace) == 0:
                continue

            self.start_nodes.add(trace[0])
            self.end_nodes.add(trace[-1])

            self.add_node(trace[0])
            self.add_node(trace[-1])

            for i in range(len(trace) - 1):
                self.add_edge(trace[i], trace[i + 1], frequency)

    def add_edge(
        self, source: str | int, destination: str | int, weight: int = 1
    ) -> None:

        if weight <= 0:
            raise ValueError("Weight must be a positive integer.")

        if not self.contains_node(source):
            self.add_node(source)

        if not self.contains_node(destination):
            self.add_node(destination)

        if source not in self.successor_list:
            self.successor_list[source] = set()

        if destination not in self.predecessor_list:
            self.predecessor_list[destination] = set()

        self.successor_list[source].add(destination)
        self.predecessor_list[destination].add(source)

    def add_node(self, node: str | int) -> None:
        if node not in self.successor_list:
            self.successor_list[node] = set()

        if node not in self.predecessor_list:
            self.predecessor_list[node] = set()

    # TODO: update to new internal dfg structure
    def get_connected_components(self) -> list[set[str | int]]:
        connected_components = []
        visited = set()

        for node in self.nodes:
            if node not in visited:
                component = self.__bfs(node)
                connected_components.append(component)
                visited.update(component)

        return connected_components

    # TODO: update to new internal dfg structure
    def __bfs(self, starting_node: str | int) -> set[str | int]:
        """Breadth-first search to find all reachable nodes from a starting node, without considering the direction of the edges."""
        queue = deque([starting_node])
        visited = set([starting_node])

        while queue:
            current_node = queue.popleft()

            for node in self.nodes:
                if node not in visited and (
                    (current_node, node) in self.edges
                    or (node, current_node) in self.edges
                ):
                    queue.append(node)
                    visited.add(node)

        return visited

    def get_successors(self, node: str | int) -> set[str | int]:
        return self.successor_list.get(node, set())

    def get_predecessors(self, node: str | int) -> set[str | int]:
        return self.predecessor_list.get(node, set())

    def get_nodes(self) -> set[str | int]:
        return self.successor_list.keys()

    def get_edges(self) -> dict[tuple[str | int, str | int], int]:
        edges = set()
        for source, destinations in self.successor_list.items():
            for destination in destinations:
                edges.add((source, destination))
        return edges

    def get_start_nodes(self) -> set[str | int]:
        return self.start_nodes

    def get_end_nodes(self) -> set[str | int]:
        return self.end_nodes

    def is_in_start_nodes(self, node: str | int) -> bool:
        return node in self.start_nodes

    def is_in_end_nodes(self, node: str | int) -> bool:
        return node in self.end_nodes

    def contains_node(self, node: str | int) -> bool:
        return node in self.successor_list.keys()

    def contains_edge(self, source: str | int, destination: str | int) -> bool:
        return destination in self.successor_list.get(source, set())

    def get_reachable_nodes(self, node: str | int) -> set[str | int]:
        queue = deque([node])
        visited = set([node])

        while queue:
            current_node = queue.popleft()

            for node in self.nodes:
                if node not in visited and (current_node, node) in self.edges:
                    queue.append(node)
                    visited.add(node)

        return visited
