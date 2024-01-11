from graphviz import Digraph
import numpy as np
from mining_algorithms.ddcal_clustering import DensityDistributionClusterAlgorithm

class FuzzyMining():
    def __init__(self, cases):
        self.cases = cases
        self.min_node_size = 1.5
        # self.events contains all events(unique!), appearance_activities are dictionaries, events:appearances ex. {'a':3, ...}
        self.events, self.appearance_activities = self.__filter_all_events()
        self.succession_matrix = self.__create_succession_matrix()
        self.correlation_of_nodes = self.__create_correlation_dependency_matrix()
        self.significance_of_nodes = self.__calculate_significance()
        #self.dependency_matrix = self.calculate_dependency_matrix()

        # style of clusterd nodes
        #graph.node(str(node), label=str(node) + "\n" + str(node_freq), width=str(w), height=str(h), shape="octagon", style="filled", fillcolor="#6495ED", color="black")

    def create_graph_with_graphviz(self, significance, correlation):
        graph = Digraph
        cluster = DensityDistributionClusterAlgorithm(list(self.appearance_activities.values()))
        """ if we have a dictionary like dict={'a':123, 'c': 234, 'e': 345, 'b': 433, 'd': 456}
         after using cluster.sorted_data we get a sorted array[123, 234, 345, 433, 456]
         after using cluster.labels_sorted_data we get a normalized array with float numbers
         minimum value starts with 0.0 and the greatest value has 5.0 in this case [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        """
        nodes_sorted = list(cluster.sorted_data)
        freq_labels_sorted = list(cluster.labels_sorted_data)

        # read all event_nodes and create
        for node in self.events:
            node_freq = self.appearance_activities.get(node)
            node_width = freq_labels_sorted[nodes_sorted.index(node_freq)]/2 + self.min_node_size
            node_height = node_width/2

            graph.node(str(node), label= str(node) + "\n" + str(node_freq), width = str(node_width), height = str(node_height), shape = "box", style = "octagon", fillcolor="#6495ED")

            # TODO cluster the edge thickness based on frequency

    def __calculate_significance(self):
        # find the most frequently node from of all events
        max_value = max(self.appearance_activities.values())

        """ to calculate the signification, we have to divide each nodes appearance by the most frequently node number
        asked ChatGpt how to do this"""
        dict = {key: value / max_value for key, value in self.appearance_activities.items()}
        return dict
    def __filter_all_events(self):
        dic = {}
        for trace in self.cases:
            for activity in trace:
                # chatGpt asked for doing this, if activity already in dictionary increase value + 1
                dic[activity] = dic.get(activity, 0) + 1
        # list of all unique activities
        activities = list(dic.keys())

        # returns activities "a", "b" ... and dic: a: 4, a has 4-appearances
        return activities, dic
    def __create_succession_matrix(self):
        """ 2D matrix a, b, c => 3x3 matrix example below
        #   a b c d
        # a 0 3 1 0
        # b 0 1 3 0
        # c 0 1 0 3
        # d 0 0 0 0
        """
        succession_matrix = np.zeros((len(self.events), len(self.events)))
        for trace in self.cases:
            index_x = -1
            for element in trace:
                if index_x < 0:
                    index_x += 1
                    continue
                x = self.events.index(trace[index_x])
                y = self.events.index(element)
                succession_matrix[x][y] += 1
                index_x += 1
        return succession_matrix

    def __create_correlation_dependency_matrix(self):
        # create a matrix with the same shape and fill it with zeros
        significance_matrix = np.zeros(self.succession_matrix.shape)
        y = 0
        for row in self.succession_matrix:
            # find max value on each row
            #max_value_in_row = max(row)
            # sum of outgoing edges means correlation of the node(row)
            sum_of_outgoing_edges = sum(row)
            x = 0
            for i in row:
                # divide each value by max value
                if i == 0 and self.succession_matrix[y][x] == 0:
                    significance_matrix[y][x] = 0.0
                else:
                    significance_matrix[y][x] = self.succession_matrix[y][x]/sum_of_outgoing_edges
                x+=1
            y+=1

        return significance_matrix

    def calculate_correlation_dependency_matrix(self, correlation):
        dependency_matrix = np.zeros(self.succession_matrix.shape)
        y = 0
        for row in self.correlation_of_nodes:
            x = 0
            for i in row:
                    if self.correlation_of_nodes[y][x]>= correlation:
                        dependency_matrix[y][x]+=1
                    x += 1
            y += 1

        return dependency_matrix

    def calculate_significance_dependency(self, significance):
        dict={}
        keys = list(self.significance_of_nodes.keys())
        values = list(self.significance_of_nodes.values())

        for i in range(len(keys)):
            if values[i] >= significance:
                dict[keys[i]] = values[i]
        return dict