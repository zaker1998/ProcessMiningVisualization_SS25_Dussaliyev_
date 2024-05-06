import graphviz
from exceptions.graph_exceptions import (
    DuplicateNodeException,
    DuplicateEdgeException,
    NodeDoesNotExistException,
    EdgeDoesNotExistException,
    InvalidNodeNameException,
)


class Node:

    def __init__(
        self,
        id: str | int,
        label: str = "",
        data: dict[str, str | int | float] = None,
    ) -> None:
        self.id: str = str(id)
        if label:
            self.label: str = label
        else:
            self.label: str = str(id)
        self.__data: dict[str, str | int | float] = data

    def get_label(self) -> str:
        return self.label

    def get_id(self) -> str:
        return self.id

    def get_data(self) -> dict[str, str | int | float]:
        return self.__data

    def get_data_from_key(self, key: str) -> str | int | float:
        if not self.__data:
            return None
        if key not in self.__data:
            return None
        return self.__data[key]


class Edge:
    def __init__(
        self,
        source: str | int,
        destination: str | int,
        weight: int = 1,
    ) -> None:
        self.source = str(source)
        self.destination = str(destination)
        self.weight = weight

    def get_edge(self) -> tuple[str, str, int]:
        return (self.source, self.destination, self.weight)


class BaseGraph:

    colon_substitute: str = "___"

    def __init__(
        self,
        **graph_attributes,
    ) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: dict[tuple[str, str], Edge] = {}

        self.graph = graphviz.Digraph()

        self.graph.attr("graph", **graph_attributes)

    def add_node(
        self,
        id: str | int,
        label: str = "",
        data: dict[str, str | int | float] = None,
        **node_attributes,
    ) -> None:

        if self.colon_substitute in str(id):
            raise InvalidNodeNameException(id)

        if self.contains_node(id):
            raise DuplicateNodeException(id)

        node = Node(id, label, data)
        self.nodes[node.get_id()] = node

        if "filled" not in node_attributes.get("style", ""):
            if "style" in node_attributes:
                node_attributes["style"] += ", filled"
            else:
                node_attributes["style"] = "filled"

        graphviz_id = self.substitiute_colons(node.get_id())
        self.graph.node(graphviz_id, node.get_label(), **node_attributes)

    def add_start_node(self, id: str = "Start") -> None:
        self.add_node(id, shape="circle", style="filled, bold", fillcolor="green")

    def add_end_node(self, id: str = "End") -> None:
        self.add_node(id, shape="doublecircle", style="filled, bold", fillcolor="red")

    def add_starting_edges(
        self,
        nodes: list[str | int],
        starting_node: str = "Start",
        weights: list[int] = None,
        **edge_attributes,
    ) -> None:
        if not nodes:
            return

        if "penwidth" not in edge_attributes:
            edge_attributes["penwidth"] = "0.1"

        for node in nodes:
            if weights:
                self.add_edge(
                    starting_node,
                    node,
                    weights[nodes.index(node)],
                    **edge_attributes,
                )
            else:
                self.add_edge(starting_node, node, weight=None, **edge_attributes)

    def add_ending_edges(
        self,
        nodes: list[str | int],
        ending_node: str = "End",
        weights: list[int] = None,
        **edge_attributes,
    ) -> None:
        if not nodes:
            return

        if "penwidth" not in edge_attributes:
            edge_attributes["penwidth"] = "0.1"

        for node in nodes:
            if weights:
                self.add_edge(
                    node, ending_node, weights[nodes.index(node)], **edge_attributes
                )
            else:
                self.add_edge(node, ending_node, weight=None, **edge_attributes)

    def add_edge(
        self,
        source_id: str | int,
        target_id: str | int,
        weight: int = 1,
        **edge_attributes,
    ) -> None:
        if not self.contains_node(source_id):
            raise NodeDoesNotExistException(source_id)

        if not self.contains_node(target_id):
            raise NodeDoesNotExistException(target_id)

        if self.contains_edge(source_id, target_id):
            raise DuplicateEdgeException(source_id, target_id)

        edge = Edge(source_id, target_id, weight)
        self.edges[(edge.source, edge.destination)] = edge

        if weight == None:
            label = ""
        else:
            label = str(weight)

        graphviz_source_id = self.substitiute_colons(edge.source)
        graphviz_target_id = self.substitiute_colons(edge.destination)

        self.graph.edge(
            graphviz_source_id,
            graphviz_target_id,
            label=label,
            **edge_attributes,
        )

    def get_node(self, id: str | int) -> Node:
        node_id = str(id).replace(self.colon_substitute, ":")
        if not self.contains_node(node_id):
            raise NodeDoesNotExistException(node_id)
        return self.nodes[str(node_id)]

    def get_edge(self, source: str | int, destination: str | int) -> Edge:
        source_id = str(source).replace(self.colon_substitute, ":")
        destination_id = str(destination).replace(self.colon_substitute, ":")
        if not self.contains_edge(source_id, destination_id):
            raise EdgeDoesNotExistException(source_id, destination_id)
        return self.edges[(source_id, destination_id)]

    def contains_node(self, id: str | int) -> bool:
        return str(id) in self.nodes

    def contains_edge(self, source: str | int, destination: str | int) -> bool:
        edge = (str(source), str(destination))
        return edge in self.edges

    def get_nodes(self) -> list[Node]:
        return list(self.nodes.values())

    def get_node_ids(self) -> list[str]:
        return list(self.nodes.keys())

    def get_edges(self) -> list[Edge]:
        return list(self.edges.values())

    def get_graphviz_string(self) -> str:
        return self.graph.source

    def get_graphviz_graph(self) -> graphviz.Digraph:
        return self.graph

    def node_to_string(self, id: str) -> tuple[str, str]:
        node = self.get_node(id)
        description = f"**Event:** {node.get_id()}"
        if node.get_data():
            for key, value in node.get_data().items():
                description += f"\n**{key}:** {value}"
        return node.get_id(), description

    def substitiute_colons(self, string: str) -> str:
        return string.replace(":", self.colon_substitute)

    def substitute_colons_back(self, string: str) -> str:
        return string.replace(self.colon_substitute, ":")
