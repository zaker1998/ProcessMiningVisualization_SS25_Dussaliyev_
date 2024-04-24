from mining_algorithms.base_mining import BaseMining
from utils.transformations import cases_list_to_dict
from logs.splits import (
    exclusive_split,
    parallel_split,
    sequence_split,
    loop_split,
)
from graphs.cuts import exclusive_cut, parallel_cut, sequence_cut, loop_cut
from graphs.dfg import DFG
from graphs.visualization.inductive_graph import InductiveGraph
from logs.filters import filter_events, filter_traces


class InductiveMining(BaseMining):
    def __init__(self, log):
        super().__init__(log)
        self.node_sizes = {k: self.calulate_node_size(k) for k in self.events}
        self.activity_threshold = 0.0
        self.traces_threshold = 0.2
        self.filtered_log = None

    def generate_graph(self, activity_threshold, traces_threshold):
        self.activity_threshold = activity_threshold
        self.traces_threshold = traces_threshold

        events_to_remove = self.get_events_to_remove(activity_threshold)
        min_traces_frequency = self.calulate_minimum_traces_frequency(traces_threshold)

        filtered_log = filter_traces(self.log, min_traces_frequency)
        filtered_log = filter_events(filtered_log, events_to_remove)

        if filtered_log == self.filtered_log:
            return

        self.filtered_log = filtered_log

        process_tree = self.inductive_mining(self.filtered_log)
        self.graph = InductiveGraph(
            process_tree,
            frequency=self.appearance_frequency,
            node_sizes=self.node_sizes,
        )

    def inductive_mining(self, log):
        if tree := self.base_cases(log):
            return tree

        if tuple() not in log:
            if partitions := self.calulate_cut(log):
                operation = partitions[0]
                return (operation, *list(map(self.inductive_mining, partitions[1:])))

        return self.fallthrough(log)

    def base_cases(self, log):
        if len(log) > 1:
            return None

        if len(log) == 1:
            trace = list(log.keys())[0]
            if len(trace) == 0:
                return "tau"
            if len(trace) == 1:
                return trace[0]

        return None

    def calulate_cut(self, log):
        dfg = DFG(log)

        if partitions := exclusive_cut(dfg):
            return ("xor", *exclusive_split(log, partitions))
        elif partitions := sequence_cut(dfg):
            return ("seq", *sequence_split(log, partitions))
        elif partitions := parallel_cut(dfg):
            return ("par", *parallel_split(log, partitions))
        elif partitions := loop_cut(dfg):
            return ("loop", *loop_split(log, partitions))

        return None

    def fallthrough(self, log):
        log_alphabet = self.get_log_alphabet(log)

        # if there is a empty trace in the log
        # make an xor split with tau and the inductive mining of the log without the empty trace
        if tuple() in log:
            empty_log = {tuple(): log[tuple()]}
            del log[tuple()]
            return ("xor", self.inductive_mining(empty_log), self.inductive_mining(log))

        # if there is a single event in the log
        # and it occures more than once in a trace
        # make a loop split with the event and tau
        # the event has to occure more than once in a trace,
        #  otherwise it would be a base case
        if len(log_alphabet) == 1:

            return ("loop", list(log_alphabet)[0], "tau")

        # if there are multiple events in the log
        # return a flower model with all the events
        return ("loop", "tau", *log_alphabet)

    def get_log_alphabet(self, log):
        return set([event for case in log for event in case])

    def get_activity_threshold(self):
        return self.activity_threshold

    def get_traces_threshold(self):
        return self.traces_threshold
