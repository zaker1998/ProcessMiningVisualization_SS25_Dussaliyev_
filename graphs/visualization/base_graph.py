import graphviz


class Node:
    def __init__(
        self,
        id: str | int,
        label: str = "",
        data: dict[str, str | int] = None,
    ) -> None:
        self.id = id
        if label:
            self.label = label
        else:
            self.label = str(id)
        self._data = data

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


class Edge:
    def __init__(
        self,
        source: str | int,
        destination: str | int,
        weight: int = 1,
    ) -> None:
        self.source = source
        self.destination = destination
        self.weight = weight

    def get_edge(self) -> tuple[str | int, str | int, int]:
        return (self.source, self.destination, self.weight)


class BaseGraph:
    def __init__(
        self,
        directed: bool = True,
        graph_attributes: dict[str, str] = None,
        global_node_attributes: dict[str, str] = None,
        global_edge_attributes: dict[str, str] = None,
    ) -> None:
        self.directed = directed
        self.nodes = {}
        self.edges = {}

        __graph_attributes = graph_attributes or {}
        __global_node_attributes = global_node_attributes or {}
        __global_edge_attributes = global_edge_attributes or {}

        self.graph = (
            graphviz.Digraph(**graph_attributes)
            if directed
            else graphviz.Graph(**graph_attributes)
        )

        self.graph.attr("node", **__global_node_attributes)
        self.graph.attr("edge", **__global_edge_attributes)

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

        __node_attributes = node_attributes or {}

        self.graph.node(str(id), node.get_label(), **__node_attributes)

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

        __edge_attributes = edge_attributes or {}
        self.graph.edge(
            str(edge.source),
            str(edge.destination),
            label=str(edge.weight),
            **__edge_attributes,
        )

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
        return self.graph.source
