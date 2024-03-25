from controllers.AlgorithmControllers import AlgorithmController
from mining_algorithms.fuzzy_mining import FuzzyMining


class FuzzyMiningController(AlgorithmController):
    significance = 0.0
    correlation = 0.0
    edge_cutoff = 0.0
    utility_ratio = 0.0

    def __init__(self, model=None):
        self.model = model

    def create_empty_model(self, cases):
        return FuzzyMining(cases)

    def perform_mining(self) -> None:
        self.model.create_graph_with_graphviz(
            self.significance, self.correlation, self.edge_cutoff, self.utility_ratio
        )

    def set_significance(self, significance: float) -> None:
        self.significance = significance

    def set_correlation(self, correlation: float) -> None:
        self.correlation = correlation

    def set_edge_cutoff(self, edge_cutoff: float) -> None:
        self.edge_cutoff = edge_cutoff

    def set_utility_ratio(self, utility_ratio: float) -> None:
        self.utility_ratio = utility_ratio

    def get_significance(self):
        return self.model.get_significance()

    def get_correlation(self):
        return self.model.get_correlation()

    def get_edge_cutoff(self):
        return self.model.get_edge_cutoff()

    def get_utility_ratio(self):
        return self.model.get_utility_ratio()
