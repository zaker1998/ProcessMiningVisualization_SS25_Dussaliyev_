from abc import ABC, abstractmethod
from utils.transformations import dataframe_to_cases_list


class AlgorithmController(ABC):
    model = None

    @abstractmethod
    def perform_mining(self) -> None:
        raise NotImplementedError("perform_mining() method not implemented")

    @abstractmethod
    def create_empty_model(self, cases):
        raise NotImplementedError("create_empty_model() method not implemented")

    @abstractmethod
    def have_parameters_changed(self):
        raise NotImplementedError("have_parameters_changed() method not implemented")

    def __create_cases_from_df(
        self, df, timestamp_col, activity_col, cases_col, **additional_cols
    ):
        cases = dataframe_to_cases_list(df, timestamp_col, cases_col, activity_col)
        return cases

    def get_model(self):
        return self.model

    def set_model(self, model):
        self.model = model

    def get_graph(self):
        return self.model.get_graph()

    def create_model(
        self, df, timestamp_col, activity_col, cases_col, **additional_cols
    ):
        if self.model is not None:
            raise ValueError("The model is already set. To change it, use set_model()")
        cases = self.__create_cases_from_df(
            df, timestamp_col, activity_col, cases_col, **additional_cols
        )
        self.model = self.create_empty_model(cases)
        return self.perform_mining()
