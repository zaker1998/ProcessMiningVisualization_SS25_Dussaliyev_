from collections import deque


class DFG:
    """Implementation of a Directly Follows Graph (DFG)"""

    def __init__(self, log: list[list[str]]) -> None:
        self.start_nodes: set[str | int] = set()
        self.end_nodes: set[str | int] = set()
        self.nodes: set[str | int] = set()
        self.edges: dict[tuple[str | int, str | int], int] = dict()
        self.__build_graph_from_log(log)

    def __build_graph_from_log(self, log: list[list[str]]) -> None:
        for trace in log:
            if len(trace) == 0:
                continue

            self.start_nodes.add(trace[0])
            self.end_nodes.add(trace[-1])

            for i in range(len(trace) - 1):
                self.add_edge(trace[i], trace[i + 1])

    def add_edge(
        self, source: str | int, destination: str | int, weight: int = 1
    ) -> None:

        if weight <= 0:
            raise ValueError("Weight must be a positive integer.")

        if source not in self.nodes:
            self.nodes.add(source)

        if destination not in self.nodes:
            self.nodes.add(destination)

        if (source, destination) in self.edges:
            self.edges[(source, destination)] += weight
        else:
            self.edges[(source, destination)] = weight

    def add_node(self, node: str | int) -> None:
        self.nodes.add(node)

    def get_connected_components(self) -> list[set[str | int]]:
        connected_components = []
        visited = set()

        for node in self.nodes:
            if node not in visited:
                component = self.__bfs(node)
                connected_components.append(component)
                visited.update(component)

        return connected_components

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

    def get_nodes(self) -> set[str | int]:
        return self.nodes

    def get_edges(self) -> dict[tuple[str | int, str | int], int]:
        return self.edges

    def get_start_nodes(self) -> set[str | int]:
        return self.start_nodes

    def get_end_nodes(self) -> set[str | int]:
        return self.end_nodes

    def is_in_start_nodes(self, node: str | int) -> bool:
        return node in self.start_nodes

    def is_in_end_nodes(self, node: str | int) -> bool:
        return node in self.end_nodes

    def contains_node(self, node: str | int) -> bool:
        return node in self.nodes

    def contains_edge(self, source: str | int, destination: str | int) -> bool:
        return (source, destination) in self.edges
