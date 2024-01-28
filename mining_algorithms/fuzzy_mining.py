from graphviz import Digraph
import numpy as np
from mining_algorithms.ddcal_clustering import DensityDistributionClusterAlgorithm

class FuzzyMining():
    def __init__(self, cases):
        self.cases = cases
        self.min_node_size = 1.5
        self.minimum_correlation = 0.7
        # self.events contains all events(unique!), appearance_activities are dictionaries, events:appearances ex. {'a':3, ...}
        self.events, self.appearance_activities = self.__filter_all_events()
        self.succession_matrix = self.__create_succession_matrix()
        self.correlation_of_nodes = self.__create_correlation_dependency_matrix()
        self.significance_of_nodes = self.__calculate_significance()
        self.node_significance_matrix = self.__calculate_node_significance_matrix(self.significance_of_nodes)
        self.clustered_nodes = None
    """  
        Info about DensityDistributionClusterAlgorithm DDCAL:
         If we have a dictionary like dict={'a':123, 'c': 234, 'e': 345, 'b': 433, 'd': 456}
         after using cluster.sorted_data we get a sorted array[123, 234, 345, 433, 456]
         after using cluster.labels_sorted_data we get a normalized array with float numbers
         minimum value starts with 0.0 and the greatest value has 5.0 in this case [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    """
    def create_graph_with_graphviz(self, significance, edge_cutoff, utility_ratio):
        #self.correlation_of_nodes = self.__calculate_correlation_dependency_matrix(correlation)
        graph = Digraph()
        cluster = DensityDistributionClusterAlgorithm(list(self.appearance_activities.values()))
        nodes_sorted = list(cluster.sorted_data)
        freq_labels_sorted = list(cluster.labels_sorted_data)
        print("Sign: " + str(significance))
        print("Succession: " + "\n" + str(self.succession_matrix))
        # 1 Rule remove less significant and less correlated nodes
        self.corr_after_first_rule, self.sign_after_first_rule = self.__calculate_first_rule(self.events, self.correlation_of_nodes, self.node_significance_matrix, significance)
        # returns a list of significant nodes e.g ['a', 'b', 'd'], not relevant nodes are not included
        nodes_after_first_rule = self.__calculate_significant_nodes(self.corr_after_first_rule)

        # 2 Rule less significant but highly correlated nodes are going to be clustered
        clustered_nodes_after_sec_rule = self.__calculate_clustered_nodes(nodes_after_first_rule, self.corr_after_first_rule, self.sign_after_first_rule, significance)
        print("Clustered nodes: " + str(clustered_nodes_after_sec_rule))
        list_of_clustered_nodes = self.__convert_clustered_nodes_to_list(clustered_nodes_after_sec_rule)
        print(list_of_clustered_nodes)

        # significance after clustering
        sign_after_sec_rule = self.__update_significance_matrix(self.sign_after_first_rule, clustered_nodes_after_sec_rule)
        print(sign_after_sec_rule)
        self.sign_dict = self.__get_significance_dict_after_clustering(sign_after_sec_rule)
        print("Sign after: " + str(self.sign_dict))

        # print clustered nodes
        self.__add_clustered_nodes_to_graph(graph, clustered_nodes_after_sec_rule, self.sign_dict)
        # what is already clustered is not a normal node
        self.__add_normal_nodes_to_graph(graph, nodes_after_first_rule, list_of_clustered_nodes, self.appearance_activities)

        for i in range(len(self.events)):
            for j in range(len(self.events)):
                # not sure if this is the right solution for showing edges for each node/cluster
                if self.corr_after_first_rule[i][j] > 0.0:
                    edge_thickness = 0.1
                    # cluster -> cluster
                    if self.events[i] in list_of_clustered_nodes and self.events[j] in list_of_clustered_nodes:
                        current_cluster = self.__get_clustered_node(clustered_nodes_after_sec_rule, self.events[i])
                        next_cluster = self.__get_clustered_node(clustered_nodes_after_sec_rule, self.events[j])
                        graph.edge(current_cluster, str(next_cluster), penwidth = str(edge_thickness),
                               label=str("{:.2f}".format(self.corr_after_first_rule[i][j])))
                        print("cluster -> cluster")

                    # cluster -> node
                    elif self.events[i] in list_of_clustered_nodes and self.events[j] not in list_of_clustered_nodes:
                        current_cluster = self.__get_clustered_node(clustered_nodes_after_sec_rule, self.events[i])
                        graph.edge(current_cluster, str(self.events[j]), penwidth=str(edge_thickness),
                                   label=str("{:.2f}".format(self.corr_after_first_rule[i][j])))
                        print("cluster -> node")
                    # node -> cluster
                    elif self.events[i] not in list_of_clustered_nodes and self.events[j] in list_of_clustered_nodes:
                        next_cluster = self.__get_clustered_node(clustered_nodes_after_sec_rule, self.events[j])
                        graph.edge(self.events[i], str(next_cluster), penwidth=str(edge_thickness),
                                   label=str("{:.2f}".format(self.corr_after_first_rule[i][j])))
                        print("node -> cluster")
                    # node -> node
                    else:
                        graph.edge(self.events[i], str(self.events[j]), penwidth=str(edge_thickness),
                                   label=str("{:.2f}".format(self.corr_after_first_rule[i][j])))
                        print("node -> node")

        return graph

    def __get_clustered_node(self, list_of_clustered_nodes, event):
        for cluster in list_of_clustered_nodes:
            cluster_events = cluster.split('-')
            if event in cluster_events:
                return cluster
        return None

    def __get_significance_dict_after_clustering(self, sign_after_sec_rule):
        dict = {}
        for i in range(len(sign_after_sec_rule)):
            dict[self.events[i]] = sign_after_sec_rule[i][0]
        return dict
    def __add_normal_nodes_to_graph(self, graph, nodes_after_first_rule, list_of_clustered_nodes, appearance_activities):
        min_node_size = 1.5
        cluster = DensityDistributionClusterAlgorithm(list(appearance_activities.values()))
        nodes_sorted = list(cluster.sorted_data)
        freq_labels_sorted = list(cluster.labels_sorted_data)
        for node in nodes_after_first_rule:
            if node not in list_of_clustered_nodes:
                node_freq = appearance_activities.get(node)
                node_width = freq_labels_sorted[nodes_sorted.index(node_freq)] / 2 + min_node_size
                node_height = node_width / 3

                node_sign = self.sign_dict.get(node)

                # chatgpt asked how to change fontcolor just for node_freq
                graph.node(str(node), label=f'<{node}<br/><font color="red">{node_sign}</font>>', width=str(node_width),
                           height=str(node_height), shape="box", style="filled", fillcolor='#FDFFF5')
        return graph
    def __convert_clustered_nodes_to_list(self, clustered_nodes):
        ret_nodes = []
        for event in clustered_nodes:
            cluster_events = event.split('-')
            for node in cluster_events:
                if node not in ret_nodes:
                    ret_nodes.append(node)
        #result_list = [event for sublist in clustered_nodes for word in sublist for event in word.split('-')]
        return ret_nodes
    def __update_significance_matrix(self, sign_after_first_rule, clustered_nodes_after_sec_rule):
        # go through each cluster
        # 1. find average sum of significance e.g. sig_a+sig_b/2
        # 2. don't change correlation, but consider current cluster as one node(a-b)
        for event in clustered_nodes_after_sec_rule:
            cluster_events = event.split('-')
            sign_after_first_rule = self.__calculate_sign_for_events(sign_after_first_rule, cluster_events)
        return sign_after_first_rule
    def __calculate_sign_for_events(self, significance_matrix, cluster_events):
        events_size = len(cluster_events)
        if events_size == 0:
            return significance_matrix
        sum = 0.0
        for i in range(len(self.events)):
            if self.events[i] in cluster_events:
                sum += significance_matrix[i][0]
        # put new sign for each row
        new_value = format(sum/events_size, '.2f')
        for i in range(len(self.events)):
            if self.events[i] in cluster_events:
                for j in range(len(self.events)):
                    significance_matrix[i][j] = new_value

        print("putting new value: " + str(new_value))
        return significance_matrix

    def __calculate_clustered_nodes(self, nodes_after_first_rule, corr_after_first_rule, sign_after_first_rule, significance):
        main_cluster_list = []
        less_sign_nodes = []
        global_clustered_nodes = set()
        for a in range(len(self.events)):
            # 1. Find less significant nodes
            if sign_after_first_rule[a][0] < significance and self.events[a] not in less_sign_nodes and self.events[a] in nodes_after_first_rule:
                less_sign_nodes.append(self.events[a])
        # 2. Find clusters of less significant nodes:
        for i in range(len(self.events)):
            if self.events[i] not in less_sign_nodes or self.events[i] in global_clustered_nodes:
                continue
            events_to_cluster = set()
            something_to_cluster = False
            for j in range(len(self.events)):
                # node will be checked horizontally and vertically (incoming and outgoing edges)
                # outgoing edges
                #first_possib = self.events[i] + self.events[j]
                # incoming edges
                #sec_possib = self.events[j] + self.events[i]
                # TODO put self.minimum_correlation instead of using hard coding
                if corr_after_first_rule[i][j] >= self.minimum_correlation or corr_after_first_rule[j][i] >= self.minimum_correlation:
                    events_to_cluster.add(self.events[i])
                    global_clustered_nodes.add(self.events[i])
                    if self.events[j] not in global_clustered_nodes:
                        events_to_cluster.add(self.events[j])
                        global_clustered_nodes.add((self.events[j]))
                        something_to_cluster = True

            if something_to_cluster:
                # special case if already all correlated nodes with current node clustered with other nodes, cluster
                # current node just by itself, it means all nodes already in global_clustered_nodes but not current node !

                # join events from set
                cluster = '-'.join(sorted(events_to_cluster))
                # check if permutation in cluster(true/false)
                if not self.__permutation_exists(cluster, main_cluster_list):
                    main_cluster_list.append(cluster)
            # add current node as cluster, special case - all correlated nodes already clustered!
            else:
                main_cluster_list.append(self.events[i])
        return main_cluster_list
    def __permutation_exists(self, current_cluster, main_cluster_list):
        sorted_cluster = sorted(current_cluster.split('-'))

        for cluster in main_cluster_list:
            cluster_events = cluster.split('-')
            if sorted_cluster == sorted(cluster_events):
                return True
        return False
    def __add_clustered_nodes_to_graph(self, graph, nodes, sign_dict):
        counter = 1
        for cluster in nodes:
            cluster_events = cluster.split('-')
            name = str(len(cluster_events)) + ' Elments'
            string_cluster = 'Cluster ' + str(counter)
            sign = sign_dict.get(cluster_events[0])
            print("cluster: " + str(cluster))
            graph.node(str(cluster), label=str(string_cluster) + "\n" + str(name) + "\n" + "~" + str(sign), width=str(1.5), height=str(1.0), shape="octagon", style="filled", fillcolor='#6495ED')
            counter += 1

    def __calculate_significant_nodes(self, corr_after_first_rule):
        # this function will be called after checking sign >= sign_slider therefore all nodes which are
        # not >= sign_slider will be replaced with -1. Therefor in this function will be checked if corr == -1
        ret_sign_nodes = []
        for i in range(len(self.events)):
            for j in range(len(self.events)):
                if corr_after_first_rule[i][j] != -1 and self.events[i] not in ret_sign_nodes:
                    ret_sign_nodes.append(self.events[i])
        return ret_sign_nodes
    # __cluster_based_on_significance_dependency
    def __calculate_first_rule(self, events, correlation_of_nodes, significance_of_nodes, significance):
        value_to_replace = -1
        indices_to_replace = set()
        # all possibilities minus itself
        node_correlation_poss = len(events) - 1
        for i in range(len(events)):
            counter = 0
            for j in range(len(events)):
                # remove self loops
                if i == j:
                    correlation_of_nodes[i][j] = 0.0
                    continue
                # these nodes are less significant and lowly correlated therefore have to be removed if
                # self.node_significance[i][j] < significance and self.correlation_of_nodes[i][j] < correlation and not self correlation
                # Ignore self correlation nodes for now
                if (correlation_of_nodes[i][j] < self.minimum_correlation and correlation_of_nodes[j][i] < self.minimum_correlation
                        and significance_of_nodes[i][j] < significance):
                    counter += 1
                #if correlation_of_nodes[i][j] < self.minimum_correlation:
                #    correlation_of_nodes[i][j] = 0
            if node_correlation_poss == counter:
                indices_to_replace.add(i)

        indices_to_replace = list(indices_to_replace)

        correlation_of_nodes = np.array(correlation_of_nodes)
        significance_of_nodes = np.array(significance_of_nodes)


        correlation_of_nodes[indices_to_replace, :] = value_to_replace
        correlation_of_nodes[:, indices_to_replace] = value_to_replace

        significance_of_nodes[indices_to_replace, :] = value_to_replace
        significance_of_nodes[:, indices_to_replace] = value_to_replace

        return correlation_of_nodes, significance_of_nodes


    #checks first element of each row(hr)
    def __get_first_nodes(self):
        start_nodes =[]
        for case in self.events:
            if case[0] not in start_nodes:
                start_nodes.append(case[0])

        return start_nodes

    def __get_end_nodes(self):
        end_nodes = []
        for case in self.events:
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
            new_sign = format(value/max_value, '.2f')
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
                    correlation_matrix[y][x] = format(self.succession_matrix[y][x]/sum_of_outgoing_edges, '.2f')
                x+=1
            y+=1

        return correlation_matrix

    #get just nodes which are >= significance (parameter)
    def calculate_significance_dependency(self, significance):
        dict={}
        keys = list(self.significance_of_nodes.keys())
        values = list(self.significance_of_nodes.values())

        for i in range(len(keys)):
            if values[i] >= significance:
                dict[keys[i]] = values[i]
        return dict

    def __calculate_node_significance_matrix(self, significance_values):
        ret_matrix = np.array(self.succession_matrix)
        significance_each_row = np.array(list(significance_values.values()))
        for i in range(ret_matrix.shape[1]):
            ret_matrix[:, i] = significance_each_row
        return ret_matrix
