from mining_algorithms.controller import Controller
from mining_algorithms.heuristic_miner.HeuristicMiningModel import HeuristicMiningModel
from graphs.visualization.heuristic_graph import HeuristicGraph
from mining_algorithms.heuristic_miner.heuristic_mining import HeuristicMining


class HeuristicMiningController(Controller):
    threshold = 0.5
    frequency = 1

    def __init__(self):
        self.model = HeuristicMiningModel()

    def perform_mining(self) -> None:

        cases = self.model.get_cases()

        heuristic_mining = HeuristicMining(cases)
        graph = heuristic_mining.create_dependency_graph_with_graphviz(
            self.threshold, self.frequency
        )
        max_frequency = heuristic_mining.get_max_frequency()
        self.model.set_threshold(self.threshold)
        self.model.set_frequency(self.frequency)

        self.model.set_max_frequency(max_frequency)
        self.model.set_graph(graph)

    def set_threshold(self, threshold: float) -> None:
        self.threshold = threshold

    def set_frequency(self, frequency: int) -> None:
        self.frequency = frequency

    def get_max_frequency(self):
        return self.model.get_max_frequency()
