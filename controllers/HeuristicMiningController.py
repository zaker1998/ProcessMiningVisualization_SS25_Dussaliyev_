from controllers.AlgorithmControllers import AlgorithmController
from graphs.visualization.heuristic_graph import HeuristicGraph
from mining_algorithms.heuristic_mining import HeuristicMining


class HeuristicMiningController(AlgorithmController):
    threshold = 0.5
    frequency = 1

    def __init__(self, model=None):
        self.model = model

    def create_empty_model(self, cases):
        return HeuristicMining(cases)

    def perform_mining(self) -> None:

        self.model.create_dependency_graph_with_graphviz(self.threshold, self.frequency)

    def set_threshold(self, threshold: float) -> None:
        self.threshold = threshold

    def set_frequency(self, frequency: int) -> None:
        self.frequency = frequency

    def get_max_frequency(self):
        return self.model.get_max_frequency()

    def get_frequency(self):
        return self.model.get_min_frequency()

    def get_threshold(self):
        return self.model.get_threshold()
