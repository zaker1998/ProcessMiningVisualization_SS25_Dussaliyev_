from graphs.visualization.base_graph import BaseGraph


class HeuristicGraph(BaseGraph):
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
        width, height = size
        label = f"{title}\n{frequency}"
        super().add_node(
            id=title,
            label=label,
            data=event_data,
            width=str(width),
            height=str(height),
            shape="box",
            style="rounded, filled",
            fillcolor="#FFFFFF",
        )

    # Rename
    def create_edge(
        self,
        source: str,
        destination: str,
        size: float,
        weight: int = None,
    ) -> None:
        super().add_edge(source, destination, weight, penwidth=str(size))

    def node_to_string(self, id: str) -> tuple[str, str]:
        node = self.get_node(id)
        description = f"**Event:** {node.get_id()}"
        if frequency := node.get_data_from_key("frequency"):
            description = f"""{description}\n**Frequency:** {frequency}"""
        return node.get_id(), description
