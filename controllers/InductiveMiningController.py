from controllers.AlgorithmControllers import AlgorithmController
from mining_algorithms.inductive_mining import InductiveMining
from utils.transformations import dataframe_to_cases_dict


class InductiveMiningController(AlgorithmController):
    activity_threshold = 1.0
    traces_threshold = 1

    def __init__(self, model=None):
        self.model = model

    def create_empty_model(self, cases):
        return InductiveMining(cases)

    def have_parameters_changed(self):
        return (
            self.get_activity_threshold() != self.activity_threshold
            or self.get_traces_threshold() != self.traces_threshold
        )

    def perform_mining(self) -> None:
        if self.get_graph() is not None and not self.have_parameters_changed():
            return
        self.model.generate_graph(self.activity_threshold, self.traces_threshold)

    def set_activity_threshold(self, value):
        self.activity_threshold = value

    def get_activity_threshold(self):
        return self.model.get_activity_threshold()

    def set_traces_threshold(self, value):
        self.traces_threshold = value

    def get_traces_threshold(self):
        return self.model.get_traces_threshold()
