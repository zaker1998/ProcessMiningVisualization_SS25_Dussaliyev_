import graphviz


class Node:
    def __init__(
        self,
        id: str | int,
        label: str = "",
        data: dict[str, str | int] = None,
        node_attributes: dict[str, str] = None,
    ) -> None:
        self.id = id
        if label:
            self.label = label
        else:
            self.label = str(id)
        self._data = data
        self._node_attributes = node_attributes

    def get_label(self) -> str:
        return self.label

    def get_id(self) -> str | int:
        return self.id

    def get_data(self) -> dict[str, str | int]:
        return self._data

    def get_data_from_key(self, key: str) -> str | int:
        if key not in self._data:
            return None
        return self._data[key]

    def get_node_attributes(self) -> dict[str, str]:
        return self._node_attributes


class Edge:
    def __init__(
        self,
        source: str | int,
        destination: str | int,
        weight: int = 1,
        edge_attributes: dict[str, str] = None,
    ) -> None:
        self.source = source
        self.destination = destination
        self.weight = weight
        self.edge_attributes = edge_attributes

    def get_edge(self) -> tuple[str | int, str | int, int]:
        return (self.source, self.destination, self.weight)


class BaseGraph:
    def __init__(
        self,
        directed: bool = True,
        global_node_attributes: dict[str, str] = None,
        global_edge_attributes: dict[str, str] = None,
    ) -> None:
        self.directed = directed
        self.nodes = {}
        self.edges = {}
        self._global_node_attributes = global_node_attributes
        self._global_edge_attributes = global_edge_attributes

    def add_node(
        self,
        id: str | int,
        label: str = "",
        data: dict[str, str | int] = None,
        node_attributes: dict[str, str] = None,
    ) -> None:
        if self.contains_node(id):
            # TODO: Add logging and use own exception types
            raise ValueError(f"Node with id {id} already exists.")
        node = Node(id, label, data, node_attributes)
        self.nodes[node.get_id()] = node

    def add_edge(
        self,
        source_id: str | int,
        target_id: str | int,
        weight: int = 1,
        edge_attributes: dict[str, str] = None,
    ) -> None:
        if source_id not in self.nodes:
            nodes[source_id] = Node(source_id)

        if target_id not in self.nodes:
            nodes[target_id] = Node(target_id)

        edge = Edge(source_id, target_id, weight, edge_attributes)
        self.edges[(edge.source, edge.destination)] = edge

    def get_node(self, id: str | int) -> Node:
        if not self.contains_node(id):
            # TODO: Add logging and use own exception types
            raise ValueError(f"Node with id {id} does not exist.")
        return self.nodes[id]

    def get_edge(self, source: str | int, destination: str | int) -> Edge:
        if not self.contains_edge(source, destination):
            # TODO: Add logging and use own exception types
            raise ValueError(f"Edge from {source} to {destination} does not exist.")
            # TODO: add result for undirected graph
        return self.edges[(source, destination)]

    def contains_node(self, id: str | int) -> bool:
        return id in self.nodes

    def contains_edge(self, source: str | int, destination: str | int) -> bool:
        if self.directed:
            return (source, destination) in self.edges
        else:
            return (source, destination) in self.edges or (
                destination,
                source,
            ) in self.edges

    def get_nodes(self) -> list[Node]:
        return list(self.nodes.values())

    def get_edges(self) -> list[Edge]:
        return list(self.edges.values())

    def get_graphviz_string(self) -> str:
        if self.directed:
            graph = graphviz.Digraph()
        else:
            graph = graphviz.Graph()

        if self._global_node_attributes:
            graph.attr(**self._global_node_attributes)

        if self._global_edge_attributes:
            graph.attr(**self._global_edge_attributes)

        for node in self.get_nodes():
            node_attributes = node.get_node_attributes() or {}
            graph.node(
                str(node.get_id()),
                label=node.get_label(),
                **node_attributes,
            )
        for edge in self.get_edges():
            edge_attributes = edge.edge_attributes or {}
            graph.edge(
                str(edge.source),
                str(edge.destination),
                label=str(edge.weight),
                **edge_attributes,
            )
        return graph.source
