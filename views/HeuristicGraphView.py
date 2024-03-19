from views.AlgorithmViewInterface import AlgorithmViewInterface
from mining_algorithms.heuristic_mining import HeuristicMining
from graphs.visualization.heuristic_graph import HeuristicGraph


class HeuristicGraphView(AlgorithmViewInterface):
    def __init__(self):
        super().__init__()

    def perform_mining(self, cases: list[list[str, ...]]) -> HeuristicGraph:
        miner = HeuristicMining(cases)
        return miner.create_dependency_graph_with_graphviz(
            self.get_slider_value("threshhold"),
            self.get_slider_value("frequency"),
        )

    def render_sliders(self):
        self.add_slider(0, 25, 1, 1, "Minimum Frequency", "frequency")
        self.add_slider(0.0, 1.0, 0.0, 0.1, "Threshhold", "threshhold")

    def get_page_title(self) -> str:
        return "Heuristic Mining"
