from mining_algorithms.base_mining import BaseMining
from utils.transformations import cases_list_to_dict


class InductiveMining(BaseMining):
    def __init__(self, log):
        super().__init__(log)

        if isinstance(log, list):
            self.log = cases_list_to_dict(log)

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
        pass

    def calulate_cut(self, log):
        pass

    def fallthrough(self, log):
        pass
