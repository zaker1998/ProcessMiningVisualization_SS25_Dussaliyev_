from graphs.visualization.base_graph import BaseGraph


class FuzzyGraph(BaseGraph):
    def __init__(
        self,
    ) -> None:
        super().__init__(rankdir="TB")

    def add_event(
        self,
        title: str,
        frequency: int,
        size: tuple[int, int],
        **event_data,
    ) -> None:
        event_data["frequency"] = frequency
        label = f"{title}\n{frequency}"
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
    ) -> None:
        super().add_edge(source, destination, weight, penwidth=str(size))

    def add_cluster(
        self,
        cluster_name: str,
        frequency: int | float,
        size: tuple[int, int],
        merged_nodes: list[str],
        **cluster_data: dict[str, str | int | float],
    ) -> None:
        cluster_data["frequency"] = frequency
        cluster_data["nodes"] = merged_nodes
        width, height = size
        label = f"{cluster_name}\n{len(merged_nodes)} Elements\n~{frequency}"
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
