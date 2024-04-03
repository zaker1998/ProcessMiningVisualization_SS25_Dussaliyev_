from controllers.AlgorithmControllers import AlgorithmController
from mining_algorithms.inductive_mining import InductiveMining
from utils.transformations import dataframe_to_cases_dict


class InductiveMiningController(AlgorithmController):

    def __init__(self, model=None):
        self.model = model

    def create_empty_model(self, cases):
        return InductiveMining(cases)

    def have_parameters_changed(self):
        return False

    def create_cases_from_df(
        self, df, timestamp_col, activity_col, cases_col, **additional_cols
    ):
        return dataframe_to_cases_dict(df, timestamp_col, cases_col, activity_col)

    def perform_mining(self) -> None:
        if self.get_graph() is not None and not self.have_parameters_changed():
            return

        self.model.generate_graph()
