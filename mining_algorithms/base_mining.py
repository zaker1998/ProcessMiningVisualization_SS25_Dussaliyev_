from mining_algorithms.ddcal_clustering import DensityDistributionClusterAlgorithm


class BaseMining:
    def __init__(self, log):
        self.log = log
        self.min_node_size = 1.5
        self.graph = None
        # self.events contains all events(unique!), appearance_activities are dictionaries, events:appearances ex. {'a':3, ...}
        self.events, self.appearance_frequency = self.__filter_out_all_events()

        """  
        Info about DensityDistributionClusterAlgorithm DDCAL:
         If we have a dictionary like dict={'a':123, 'c': 234, 'e': 345, 'b': 433, 'd': 456}
         after using cluster.sorted_data we get a sorted array[123, 234, 345, 433, 456]
         after using cluster.labels_sorted_data we get a normalized array with float numbers
         minimum value starts with 0.0 and the greatest value has 5.0 in this case [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        """
        # cluster the node sizes based on frequency
        cluster = DensityDistributionClusterAlgorithm(
            list(self.appearance_frequency.values())
        )
        self.freq_sorted = list(cluster.sorted_data)
        self.freq_labels_sorted = list(cluster.labels_sorted_data)

        self.start_nodes = self.__get_start_nodes()
        self.end_nodes = self.__get_end_nodes()

    def __filter_out_all_events(self):
        dic = {}
        for trace, frequency in self.log.items():
            for activity in trace:
                if activity in dic:
                    dic[activity] = dic[activity] + frequency
                else:
                    dic[activity] = frequency

        activities = list(dic.keys())
        return activities, dic

    def get_graph(self):
        return self.graph

    def calulate_node_size(self, node):
        scale_factor = self.get_scale_factor(node)

        width = (scale_factor / 2) + self.min_node_size
        height = width / 3
        return width, height

    def get_scale_factor(self, node):
        node_freq = self.appearance_frequency.get(node)
        scale_factor = self.freq_labels_sorted[self.freq_sorted.index(node_freq)]
        return scale_factor

    def __get_start_nodes(self):
        return set([trace[0] for trace in self.log.keys() if len(trace) > 0])

    def __get_end_nodes(self):
        return set([trace[-1] for trace in self.log.keys() if len(trace) > 0])
