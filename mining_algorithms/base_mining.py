import numpy as np
from mining_algorithms.mining_interface import MiningInterface


class BaseMining(MiningInterface):
    def __init__(self, log):
        super().__init__()
        self.log = log
        # self.events contains all events(unique!), appearance_activities are dictionaries, events:appearances ex. {'a':3, ...}
        self.events, self.appearance_frequency = self.__filter_out_all_events()
        self.event_positions = {event: i for i, event in enumerate(self.events)}
        self.succession_matrix = self.__create_succession_matrix()

        self.event_freq_sorted, self.event_freq_labels_sorted = self.get_clusters(
            list(self.appearance_frequency.values())
        )

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

    def calulate_node_size(self, node):
        scale_factor = self.get_scale_factor(node)

        width = (scale_factor / 2) + self.min_node_size
        height = width / 3
        return width, height

    def get_scale_factor(self, node):
        node_freq = self.appearance_frequency.get(node)
        scale_factor = self.event_freq_labels_sorted[
            self.event_freq_sorted.index(node_freq)
        ]
        return scale_factor

    def __get_start_nodes(self):
        return set([trace[0] for trace in self.log.keys() if len(trace) > 0])

    def __get_end_nodes(self):
        return set([trace[-1] for trace in self.log.keys() if len(trace) > 0])

    def __create_succession_matrix(self):
        succession_matrix = np.zeros((len(self.events), len(self.events)))
        for trace, frequency in self.log.items():
            indices = [self.event_positions[event] for event in trace]
            source_indices = indices[:-1]
            target_indices = indices[1:]
            # https://numpy.org/doc/stable/reference/generated/numpy.ufunc.at.html
            np.add.at(succession_matrix, (source_indices, target_indices), frequency)

        return succession_matrix

    def get_events_to_remove(self, threshold):
        if threshold > 1.0:
            threshold = 1.0
        elif threshold < 0.0:
            threshold = 0.0

        minimum_event_freq = round(max(self.appearance_frequency.values()) * threshold)

        return set(
            [
                event
                for event, freq in self.appearance_frequency.items()
                if freq < minimum_event_freq
            ]
        )

    def calulate_minimum_traces_frequency(self, threshold):
        if threshold > 1.0:
            threshold = 1.0
        elif threshold < 0.0:
            threshold = 0.0

        minimum_trace_freq = round(max(self.log.values()) * threshold)

        return minimum_trace_freq
