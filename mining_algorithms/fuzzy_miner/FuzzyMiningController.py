from mining_algorithms.controller import Controller
from mining_algorithms.fuzzy_miner.FuzzyMiningModel import FuzzyMiningModel
from graphs.visualization.fuzzy_graph import FuzzyGraph
from mining_algorithms.fuzzy_miner.fuzzy_mining import FuzzyMining


class FuzzyMiningController(Controller):
    significance = 0.0
    correlation = 0.0
    edge_cutoff = 0.0
    utility_ratio = 0.0

    def __init__(self):
        self.model = FuzzyMiningModel()

    def perform_mining(self) -> None:

        cases = self.model.get_cases()

        fuzzy_mining = FuzzyMining(cases)

        graph = fuzzy_mining.create_graph_with_graphviz(
            self.significance, self.correlation, self.edge_cutoff, self.utility_ratio
        )

        self.model.set_significance(self.significance)
        self.model.set_correlation(self.correlation)
        self.model.set_edge_cutoff(self.edge_cutoff)
        self.model.set_utility_ratio(self.utility_ratio)

        self.model.set_graph(graph)

    def set_significance(self, significance: float) -> None:
        self.significance = significance

    def set_correlation(self, correlation: float) -> None:
        self.correlation = correlation

    def set_edge_cutoff(self, edge_cutoff: float) -> None:
        self.edge_cutoff = edge_cutoff

    def set_utility_ratio(self, utility_ratio: float) -> None:
        self.utility_ratio = utility_ratio
