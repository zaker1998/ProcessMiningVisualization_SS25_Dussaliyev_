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
        self.significance_matrix = self.__calculate_significance_matrix(self.significance_of_nodes)
        #self.dependency_matrix = self.calculate_dependency_matrix()

        # style of clusterd nodes
        #graph.node(str(node), label=str(node) + "\n" + str(node_freq), width=str(w), height=str(h), shape="octagon", style="filled", fillcolor="#6495ED", color="black")

    def create_graph_with_graphviz(self, significance, edge_cutoff, utility_ratio):
        #self.correlation_of_nodes = self.__calculate_correlation_dependency_matrix(correlation)
        graph = Digraph()
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
            node_height = node_width/3
            # chatgpt asked how to change fontcolor just for node_freq
            graph.node(str(node), label=f'<{node}<br/><font color="red">{node_freq}</font>>', width=str(node_width),
                       height=str(node_height), shape="box", style="filled", fillcolor='#FDFFF5')
            #graph.node(str(node), label= str(node)+"\n" + str(node_freq), width = str(node_width), height = str(node_height), shape = "octagon", style = "filled", fillcolor='#6495ED')

            # TODO cluster the edge thickness based on frequency
        #self.filtered_events = calculate_significance_dependency(significance).keys()
        for i in range(len(self.events)):
            for j in range(len(self.events)):
                #TODO delete correlation value- hardcoded:
                """if self.correlation_of_nodes[i][j] >= 0.3:
                    edge_thickness = 0.1
                    graph.edge(str(self.events[i]), str(self.events[j]), penwidth=str(edge_thickness),
                               label=str("{:.2f}".format(float(self.correlation_of_nodes[i][j]))))"""
                if self.correlation_of_nodes[i][j] >= 0.5 and self.significance_matrix[i][j] > significance:
                    edge_thickness = 0.1
                    graph.edge(str(self.events[i]), str(self.events[j]), penwidth = str(edge_thickness),
                               label=str("{:.2f}".format(float(self.correlation_of_nodes[i][j]))))

        graph.node("start", label="start", shape='doublecircle', style='filled', fillcolor='green')
        for node in self.__get_first_nodes():
            graph.edge("start", str(node), penwidth=str(0.1))

        graph.node("end", label="end", shape = 'doublecircle', style='filled', fillcolor='red')
        for node in self.__get_end_nodes():
            graph.edge(str(node),"end", penwidth=str(0.1))

        return graph
    #checks first element of each row(hr)
    def __get_first_nodes(self):
        start_nodes =[]
        for case in self.cases:
            if case[0] not in start_nodes:
                start_nodes.append(case[0])

        return start_nodes

    def __get_end_nodes(self):
        end_nodes = []
        for case in self.cases:
            last_node_index = len(case)-1
            if case[last_node_index] not in end_nodes:
                end_nodes.append(case[last_node_index])
        return end_nodes
    """ to calculate the signification, we have to divide each nodes appearance by the most frequently node number
        asked ChatGpt how to do this"""
    def __calculate_significance(self):
        # find the most frequently node from of all events
        max_value = max(self.appearance_activities.values())
        dict = {}
        #dict = {key: value / max_value for key, value in self.appearance_activities.items()}
        for key, value in self.appearance_activities.items():
            new_sign = value/max_value
            dict[key] = new_sign
        return dict

    def __filter_all_events(self):
        dic = {}
        for trace in self.cases:
            for activity in trace:
                # chatGpt asked for doing this, if activity already in dictionary increase value + 1
                dic[activity] = dic.get(activity, 0) + 1
        # list of all unique activities
        activities = list(dic.keys())

        # returns activities "a", "b" ... and dic: a: 4, a has 4-appearances ...
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
        correlation_matrix = np.zeros(self.succession_matrix.shape)
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
                    correlation_matrix[y][x] = 0.0
                else:
                    correlation_matrix[y][x] = self.succession_matrix[y][x]/sum_of_outgoing_edges
                x+=1
            y+=1

        return correlation_matrix


    """
    def __calculate_correlation_dependency_matrix(self, correlation):
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
        """

    #get just nodes which are >= significance (parameter)
    def calculate_significance_dependency(self, significance):
        dict={}
        keys = list(self.significance_of_nodes.keys())
        values = list(self.significance_of_nodes.values())

        for i in range(len(keys)):
            if values[i] >= significance:
                dict[keys[i]] = values[i]
        return dict

    def __calculate_significance_matrix(self, significance_values):
        ret_matrix = np.array(self.succession_matrix)
        significance_each_row = np.array(list(significance_values.values()))
        for i in range(ret_matrix.shape[1]):
            ret_matrix[:, i] = significance_each_row
        return ret_matrix
