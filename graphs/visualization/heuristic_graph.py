from graphs.visualization.base_graph import BaseGraph


class HeuristicGraph(BaseGraph):
    def __init__(
        self,
    ) -> None:
        # TODO add graph attributes
        super().__init__()

    def add_event(
        title: str,
        frequency: int,
        size: tuple[int, int],
        **event_data: dict[str, str | int | float],
    ) -> None:
        event_data["frequency"] = frequency
        label = f"{title} \n {frequency}"
        width, height = size
        self.add_node(
            id=title,
            label=label,
            data=event_data,
            width=width,
            height=height,
            shape="box",
            style="rounded, filled",
            fillcolor="lightblue",
        )

    def add_edge(
        source: str,
        destination: str,
        weight: int,
        size: float,
    ) -> None:
        super().add_edge(source, destination, weight, penwidth=size)
