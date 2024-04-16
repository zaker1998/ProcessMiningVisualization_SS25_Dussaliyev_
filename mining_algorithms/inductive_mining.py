from mining_algorithms.base_mining import BaseMining
from utils.transformations import cases_list_to_dict
from utils.log_splitting import (
    exclusive_split,
    parallel_split,
    sequence_split,
    loop_split,
)
from graphs.cuts import exclusive_cut, parallel_cut, sequence_cut, loop_cut


class InductiveMining(BaseMining):
    def __init__(self, log):
        super().__init__(log)

    def generate_graph(self):
        pass

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

        if len(log) == 0:
            return "tau"

        if len(log) == 1:
            if len(log[0]) == 0:
                return "tau"
            if len(log[0]) == 1:
                return log[0][0]

        return None

    def calulate_cut(self, log):

        if partitions := exclusive_cut(log):
            return ("xor", *exclusive_split(log, partitions))
        elif partitions := sequence_cut(log):
            return ("seq", *sequence_split(log, partitions))
        elif partitions := parallel_cut(log):
            return ("parallel", *parallel_split(log, partitions))
        elif partitions := loop_cut(log):
            return ("loop", *loop_split(log, partitions))

        return None

    def fallthrough(self, log):
        pass
