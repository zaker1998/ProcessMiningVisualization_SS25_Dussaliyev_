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
        sources, targets = np.nonzero(dependency_graph)
        for source, target, weight in zip(
            sources, targets, dependency_graph[sources, targets]
        ):
            if dependency_threshold == 0:
                edge_thickness = 0.1
            else:
                edge_thickness = (
                    freq_labels_sorted[
                        freq_sorted.index(self.dependency_matrix[source][target])
                    ]
                    + self.min_edge_thickness
                )

            self.graph.create_edge(
                self.events[source],
                self.events[target],
                weight=int(weight),
                size=edge_thickness,
            )

        # add start and end nodes
        self.graph.add_start_node()
        self.graph.add_end_node()

        # add starting and ending edges from the log
        self.graph.add_starting_edges(self.start_nodes)
        self.graph.add_ending_edges(self.end_nodes)

        source_nodes = self.__get_sources_from_dependency_graph(dependency_graph)
        sink_nodes = self.__get_sinks_from_dependency_graph(dependency_graph)

        self.graph.add_starting_edges(source_nodes - self.start_nodes)
        self.graph.add_ending_edges(sink_nodes - self.end_nodes)

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
            for index in range(len(trace) - 1):
                x = mapping[trace[index]]
                y = mapping[trace[index + 1]]
                succession_matrix[x][y] += frequency
        return succession_matrix

    def __create_dependency_matrix(self):
        dependency_matrix = np.zeros(self.succession_matrix.shape)
        for y in range(self.succession_matrix.shape[0]):
            for x in range(self.succession_matrix.shape[0]):
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
        return dependency_matrix

    def __create_dependency_graph(self, dependency_treshhold, min_frequency):
        dependency_graph = np.zeros(self.dependency_matrix.shape)
        # filter out the edges that are not frequent enough or not dependent enough
        filter_matrix = (self.succession_matrix >= min_frequency) & (
            self.dependency_matrix >= dependency_treshhold
        )

        dependency_graph[filter_matrix] = self.succession_matrix[filter_matrix]

        return dependency_graph

    def __get_sources_from_dependency_graph(self, dependency_graph):
        indices = np.where((dependency_graph == 0).all(axis=0))[0]
        return set([self.events[i] for i in indices])

    def __get_sinks_from_dependency_graph(self, dependency_graph):
        indices = np.where((dependency_graph == 0).all(axis=1))[0]
        return set([self.events[i] for i in indices])
