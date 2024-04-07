import numpy as np
from mining_algorithms.ddcal_clustering import DensityDistributionClusterAlgorithm
from graphs.visualization.heuristic_graph import HeuristicGraph
from mining_algorithms.base_mining import BaseMining


class HeuristicMining(BaseMining):
    def __init__(self, log):
        super().__init__(log)
        self.succession_matrix = self.__create_succession_matrix()
        self.dependency_matrix = self.__create_dependency_matrix()

        # Graph modifiers
        self.min_edge_thickness = 1
        self.min_frequency = 1
        self.dependency_threshold = 0.5

    def create_dependency_graph_with_graphviz(
        self, dependency_threshold, min_frequency
    ):
        dependency_graph = self.__create_dependency_graph(
            dependency_threshold, min_frequency
        )
        self.dependency_threshold = dependency_threshold
        self.min_frequency = min_frequency

        # create graph
        self.graph = HeuristicGraph()
        # cluster the node sizes based on frequency

        # add nodes to graph
        for node in self.events:
            node_freq = self.appearence_frequency.get(node)
            w, h = self.calulate_node_size(node)
            self.graph.add_event(node, node_freq, (w, h))

        # cluster the edge thickness sizes based on frequency
        edge_frequencies = self.dependency_matrix.flatten()
        edge_frequencies = edge_frequencies[edge_frequencies >= 0.0]
        edge_frequencies = np.unique(edge_frequencies)
        # print(edge_frequencies)
        # TODO: move in base class if used in other algorithms
        cluster = DensityDistributionClusterAlgorithm(edge_frequencies)
        freq_sorted = list(cluster.sorted_data)
        freq_labels_sorted = list(cluster.labels_sorted_data)

        # add edges to graph
        for i in range(len(self.events)):
            for j in range(len(self.events)):
                if dependency_graph[i][j] == 1.0:
                    if dependency_threshold == 0:
                        edge_thickness = 0.1
                    else:
                        edge_thickness = (
                            freq_labels_sorted[
                                freq_sorted.index(self.dependency_matrix[i][j])
                            ]
                            + self.min_edge_thickness
                        )
                    self.graph.create_edge(
                        self.events[i],
                        self.events[j],
                        weight=int(self.succession_matrix[i][j]),
                        size=edge_thickness,
                    )
        # add start and end nodes
        self.graph.add_start_node()
        self.graph.add_end_node()

        # add starting and ending edges from the log
        self.graph.add_starting_edges(self.start_nodes)
        self.graph.add_ending_edges(self.end_nodes)

        # TODO: add startign and ending edges for nodes that are
        # 1. not reachable from the start node
        # 2. not leading to the end node

    # TODO should be max frequency of edges and not nodes
    def get_max_frequency(self):
        max_freq = 0
        for value in list(self.appearence_frequency.values()):
            if value > max_freq:
                max_freq = value
        return max_freq

    def get_min_frequency(self):
        return self.min_frequency

    def get_threshold(self):
        return self.dependency_threshold

    def __create_succession_matrix(self):
        succession_matrix = np.zeros((len(self.events), len(self.events)))
        mapping = {event: i for i, event in enumerate(self.events)}
        for trace, frequency in self.log.items():
            index_x = -1
            for element in trace:

                if index_x < 0:
                    index_x += 1
                    continue
                x = mapping[trace[index_x]]
                y = mappping[element]
                succession_matrix[x][y] += frequency
                index_x += 1
        return succession_matrix

    def __create_dependency_matrix(self):
        dependency_matrix = np.zeros(self.succession_matrix.shape)
        y = 0
        for row in self.succession_matrix:
            x = 0
            for i in row:
                if x == y:
                    dependency_matrix[x][y] = self.succession_matrix[x][y] / (
                        self.succession_matrix[x][y] + 1
                    )
                else:
                    dependency_matrix[x][y] = (
                        self.succession_matrix[x][y] - self.succession_matrix[y][x]
                    ) / (
                        self.succession_matrix[x][y] + self.succession_matrix[y][x] + 1
                    )
                x += 1
            y += 1
        return dependency_matrix

    # TODO: do not store only if edges exists, but also store the weight of the edge
    def __create_dependency_graph(self, dependency_treshhold, min_frequency):
        dependency_graph = np.zeros(self.dependency_matrix.shape)
        y = 0
        for row in dependency_graph:
            for x in range(len(row)):
                if (
                    self.dependency_matrix[y][x] >= dependency_treshhold
                    and self.succession_matrix[y][x] >= min_frequency
                ):
                    dependency_graph[y][x] += 1
            y += 1

        return dependency_graph
