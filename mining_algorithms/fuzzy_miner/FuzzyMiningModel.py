from mining_algorithms.model import Model


class FuzzyMiningModel(Model):

    def __init__(self):
        self.significance = None
        self.correlation = None
        self.edge_cutoff = None
        self.utility_ratio = None

    def get_significance(self):
        return self.significance

    def set_significance(self, significance):
        self.significance = significance

    def get_correlation(self):
        return self.correlation

    def set_correlation(self, correlation):
        self.correlation = correlation

    def get_edge_cutoff(self):
        return self.edge_cutoff

    def set_edge_cutoff(self, edge_cutoff):
        self.edge_cutoff = edge_cutoff

    def get_utility_ratio(self):
        return self.utility_ratio

    def set_utility_ratio(self, utility_ratio):
        self.utility_ratio = utility_ratio
