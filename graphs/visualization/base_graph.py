import graphviz


# TODO: Consistent behaviour if node or edge already exists or if something is not found. Either exceptions or return None. Own design decision
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
        if key not in self.__data:
            # Throw exception instead of none? Or return default value? Should be consitant throughout the code
            # own design decision!!
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
    def __init__(
        self,
        directed: bool = True,
        **graph_attributes,
    ) -> None:
        self.directed: bool = directed
        self.nodes: dict[str, Node] = {}
        self.edges: dict[tuple[str, str], Edge] = {}

        self.graph = graphviz.Digraph() if directed else graphviz.Graph()

        self.graph.attr("graph", **graph_attributes)

    def add_node(
        self,
        id: str | int,
        label: str = "",
        data: dict[str, str | int | float] = None,
        **node_attributes,
    ) -> None:
        if self.contains_node(id):
            # TODO: Add logging and use own exception types
            raise ValueError(f"Node with id {id} already exists.")
        node = Node(id, label, data)
        self.nodes[node.get_id()] = node

        self.graph.node(node.get_id(), node.get_label(), **node_attributes)

    def add_start_node(self, id: str = "Start", **node_attributes) -> None:
        if node_attributes:
            self.add_node(id, **node_attributes)
        else:
            self.add_node(id, shape="circle", style="filled", fillcolor="green")

    def add_end_node(self, id: str = "End", **node_attributes) -> None:
        if node_attributes:
            self.add_node(id, **node_attributes)
        else:
            self.add_node(id, shape="circle", style="filled, bold", fillcolor="red")

    def add_starting_edges(
        self,
        nodes: list[str | int],
        starting_node: str = "Start",
        weights: list[int] = None,
        **edge_attributes,
    ) -> None:
        if not nodes:
            return

        for node in nodes:
            if weights:
                self.add_edge(
                    starting_node,
                    node,
                    weights[nodes.index(node)],
                    **edge_attributes,
                )
            else:
                self.add_edge(starting_node, node, **edge_attributes)

    def add_ending_edges(
        self,
        nodes: list[str | int],
        ending_node: str = "End",
        weights: list[int] = None,
        **edge_attributes,
    ) -> None:
        if not nodes:
            return

        for node in nodes:
            if weights:
                self.add_edge(
                    node, ending_node, weights[nodes.index(node)], **edge_attributes
                )
            else:
                self.add_edge(node, ending_node, weight=None, **edge_attributes)

    # Need better naming to not collide with the add_edge method from inheritance
    def add_edge(
        self,
        source_id: str | int,
        target_id: str | int,
        weight: int = 1,
        **edge_attributes,
    ) -> None:
        if str(source_id) not in self.nodes:
            self.nodes[str(source_id)] = Node(source_id)

        if str(target_id) not in self.nodes:
            self.nodes[str(target_id)] = Node(target_id)

        if self.contains_edge(source_id, target_id):
            raise ValueError(f"Edge from {source_id} to {target_id} already exists.")

        edge = Edge(source_id, target_id, weight)
        self.edges[(edge.source, edge.destination)] = edge
        if weight == None:
            label = ""
        else:
            label = str(weight)

        self.graph.edge(
            edge.source,
            edge.destination,
            label=label,
            **edge_attributes,
        )

    def get_node(self, id: str | int) -> Node:
        if not self.contains_node(id):
            # TODO: Add logging and use own exception types
            raise ValueError(f"Node with id {id} does not exist.")
        return self.nodes[str(id)]

    def get_edge(self, source: str | int, destination: str | int) -> Edge:
        if not self.contains_edge(source, destination):
            # TODO: Add logging and use own exception types
            raise ValueError(f"Edge from {source} to {destination} does not exist.")
            # TODO: add result for undirected graph
        return self.edges[(str(source), str(destination))]

    def contains_node(self, id: str | int) -> bool:
        return str(id) in self.nodes

    def contains_edge(self, source: str | int, destination: str | int) -> bool:
        edge = (str(source), str(destination))
        if self.directed:
            return edge in self.edges
        else:
            return edge in self.edges or edge[::-1] in self.edges

    def get_nodes(self) -> list[Node]:
        return list(self.nodes.values())

    def get_edges(self) -> list[Edge]:
        return list(self.edges.values())

    def get_graphviz_string(self) -> str:
        return self.graph.source

    def export_graph(self, filename: str, format: str = "png") -> None:
        self.graph.render(filename, format=format, cleanup=True)
