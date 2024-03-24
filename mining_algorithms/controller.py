from mining_algorithms.model import Model
from abc import ABC, abstractmethod
from utils.transformations import dataframe_to_cases_list


class Controller(ABC):
    model: Model = None

    @abstractmethod
    def perform_mining(self) -> None:
        raise NotImplementedError("perform_mining() method not implemented")

    def __create_cases_from_df(
        self, df, timestamp_col, activity_col, cases_col, **additional_cols
    ):
        cases = dataframe_to_cases_list(df, timestamp_col, cases_col, activity_col)
        return cases

    def get_model(self) -> Model:
        return self.model

    def set_model(self, model: Model) -> None:
        if self.model is None:
            raise ValueError(
                "The model is not set. this should have been done in the constructor."
            )
        self.model = model

    def get_graph(self):
        return self.model.get_graph()

    def create_model(
        self, df, timestamp_col, activity_col, cases_col, **additional_cols
    ):
        if self.model is None:
            raise ValueError("The model is not set")

        cases = self.__create_cases_from_df(
            df, timestamp_col, activity_col, cases_col, **additional_cols
        )
        self.model.set_cases(cases)
        self.perform_mining()

    def get_model_frequency(self):
        return self.model.get_frequency()

    def get_model_threshold(self):
        return self.model.get_threshold()
