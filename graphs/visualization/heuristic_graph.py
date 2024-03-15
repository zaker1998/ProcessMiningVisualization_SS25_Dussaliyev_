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
        **event_data: dict[str, str | int | float],
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
            fillcolor="lightblue",
        )

    def add_start_node(self, title: str = "start") -> None:
        super().add_node(
            id=title,
            label=title,
            shape="circle",
            style="filled",
            fillcolor="green",
        )

    def add_end_node(self, title: str = "end") -> None:
        super().add_node(
            id=title,
            label=title,
            shape="doublecircle",
            style="filled",
            fillcolor="red",
        )

    def add_edge(
        self,
        source: str,
        destination: str,
        size: float,
        weight: int = None,
    ) -> None:
        super().add_edge(source, destination, weight, penwidth=str(size))
