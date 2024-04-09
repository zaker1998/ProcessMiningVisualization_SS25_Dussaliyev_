from graphs.visualization.base_graph import BaseGraph


class FuzzyGraph(BaseGraph):
    def __init__(
        self,
    ) -> None:
        super().__init__(rankdir="TB")

    def add_event(
        self,
        title: str,
        significance: int,
        size: tuple[int, int],
        **event_data,
    ) -> None:
        event_data["significance"] = significance
        # chatgpt asked how to change fontcolor just for node_freq
        label = f'<{title}<br/><font color="red">{significance}</font>>'
        width, height = size
        super().add_node(
            id=title,
            label=label,
            data=event_data,
            width=str(width),
            height=str(height),
            shape="box",
            style="filled",
            fillcolor="#FDFFF5",
        )

    def create_edge(
        self,
        source: str,
        destination: str,
        size: float,
        weight: int = None,
        color: str = "black",
    ) -> None:
        super().add_edge(source, destination, weight, penwidth=str(size), color=color)

    def add_cluster(
        self,
        cluster_name: str,
        significance: int | float,
        size: tuple[int, int],
        merged_nodes: list[str],
        **cluster_data: dict[str, str | int | float],
    ) -> None:
        cluster_data["significance"] = significance
        cluster_data["nodes"] = merged_nodes
        width, height = size
        label = f"{cluster_name}\n{len(merged_nodes)} Elements\n~{significance}"
        super().add_node(
            id=cluster_name,
            label=label,
            data=cluster_data,
            shape="octagon",
            style="filled",
            fillcolor="#6495ED",
            width=str(width),
            height=str(height),
        )

    def node_to_string(self, id: str) -> tuple[str, str]:
        node = self.get_node(id)
        node_name = node.get_id()
        if "cluster" in node_name.lower():
            description = f"**Cluster:** {node_name}"
        else:
            description = f"**Event:** {node_name}"

        if significance := node.get_data_from_key("significance"):
            description = f"""{description}\n**Significance:** {significance}"""

        if nodes := node.get_data_from_key("nodes"):
            description = f"""{description}\n**Clustered Nodes:** {", ".join(nodes)}"""

        return node.get_id(), description
