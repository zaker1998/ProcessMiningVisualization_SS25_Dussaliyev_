class DFG:
    """Implementation of a Directly Follows Graph (DFG)"""

    def __init__(self, log: list[list[str]]) -> None:
        self.nodes: set[str | int] = set()
        self.edges: dict[tuple[str | int, str | int], int] = dict()
        self.build_graph_from_log(log)

    def build_graph_from_log(self, log: list[list[str]]) -> None:
        # TODO: Implement this method
        pass

    def add_edge(self, source: str | int, destination: str | int) -> None:
        if source not in self.nodes:
            self.nodes.add(source)

        if destination not in self.nodes:
            self.nodes.add(destination)

        if (source, destination) in self.edges:
            self.edges[(source, destination)] += 1
        else:
            self.edges[(source, destination)] = 1

    def add_node(self, node: str | int) -> None:
        self.nodes.add(node)

    def get_nodes(self) -> set[str | int]:
        return self.nodes

    def get_edges(self) -> dict[tuple[str | int, str | int], int]:
        return self.edges
