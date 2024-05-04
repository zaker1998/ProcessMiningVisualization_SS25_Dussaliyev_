from abc import ABC
from mining_algorithms.ddcal_clustering import DensityDistributionClusterAlgorithm


class MiningInterface(ABC):

    def __init__(self):
        self.graph = None
        self.min_node_size = 1.5

    def get_clusters(self, frequency):
        try:
            cluster = DensityDistributionClusterAlgorithm(frequency)
            return list(cluster.sorted_data), list(cluster.labels_sorted_data)
        except ZeroDivisionError as e:
            # TODO: use logging
            print(e)
            return [frequency[0]], [1.0]

    def get_graph(self):
        return self.graph
