from controllers.AlgorithmControllers import AlgorithmController
from mining_algorithms.inductive_mining import InductiveMining
from utils.transformations import dataframe_to_cases_dict


class InductiveMiningController(AlgorithmController):
    activity_threshold = 1.0
    minimum_traces_frequency = 1

    def __init__(self, model=None):
        self.model = model

    def create_empty_model(self, cases):
        return InductiveMining(cases)

    def have_parameters_changed(self):
        return (
            self.get_activity_threshold() != self.activity_threshold
            or self.get_minimum_traces_frequency() != self.minimum_traces_frequency
        )

    def perform_mining(self) -> None:
        if self.get_graph() is not None and not self.have_parameters_changed():
            return
        self.model.generate_graph(
            self.activity_threshold, self.minimum_traces_frequency
        )

    def set_activity_threshold(self, value):
        self.activity_threshold = value

    def get_activity_threshold(self):
        return self.model.get_activity_threshold()

    def set_minimum_traces_frequency(self, value):
        self.minimum_traces_frequency = value

    def get_minimum_traces_frequency(self):
        return self.model.get_mininum_traces_frequency()

    def get_maximum_trace_frequency(self):
        return self.model.get_maximum_trace_frequency()
