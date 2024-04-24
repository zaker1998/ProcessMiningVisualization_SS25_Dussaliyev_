import numpy as np
from mining_algorithms.ddcal_clustering import DensityDistributionClusterAlgorithm
from graphs.visualization.heuristic_graph import HeuristicGraph
from mining_algorithms.base_mining import BaseMining


class HeuristicMining(BaseMining):
    def __init__(self, log):
        super().__init__(log)
        self.dependency_matrix = self.__create_dependency_matrix()

        # Graph modifiers
        self.min_edge_thickness = 1
        self.min_frequency = 1
        self.dependency_threshold = 0.5
        self.max_frequency = int(np.max(self.succession_matrix))

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
            node_freq = self.appearance_frequency.get(node)
            w, h = self.calulate_node_size(node)
            self.graph.add_event(node, node_freq, (w, h))

        # add edges to graph
        sources, targets = np.nonzero(dependency_graph)
        for source, target, weight in zip(
            sources, targets, dependency_graph[sources, targets]
        ):
            if dependency_threshold == 0:
                edge_thickness = 0.1
            else:
                edge_thickness = (
                    self.get_edge_scale_factor(source, target) + self.min_edge_thickness
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

    def get_max_frequency(self):
        # +1 to be able to remove all edges, not sure if it's correct or needed, but all edges can be deleted with this setting
        return self.max_frequency + 1

    def get_min_frequency(self):
        return self.min_frequency

    def get_threshold(self):
        return self.dependency_threshold

    def __create_dependency_matrix(self):
        dependency_matrix = np.zeros(self.succession_matrix.shape)
        np.fill_diagonal(dependency_matrix, 1.0)

        non_diagonal_indices = np.where(dependency_matrix == 0)
        diagonal_indices = np.diag_indices(dependency_matrix.shape[0])

        dependency_matrix[diagonal_indices] = self.succession_matrix[
            diagonal_indices
        ] / (self.succession_matrix[diagonal_indices] + 1)

        x, y = non_diagonal_indices

        dependency_matrix[x, y] = (
            self.succession_matrix[x, y] - self.succession_matrix[y, x]
        ) / (self.succession_matrix[x, y] + self.succession_matrix[y, x] + 1)
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
        indices = self.__get_all_axis_with_all_zero(dependency_graph, axis=0)
        return set([self.events[i] for i in indices])

    def __get_sinks_from_dependency_graph(self, dependency_graph):
        indices = self.__get_all_axis_with_all_zero(dependency_graph, axis=1)
        return set([self.events[i] for i in indices])

    def __get_all_axis_with_all_zero(self, dependency_graph, axis=0):
        filter_matrix = dependency_graph == 0
        # edges from and to the same node are not considered
        np.fill_diagonal(filter_matrix, True)
        return np.where(filter_matrix.all(axis=axis))[0]
