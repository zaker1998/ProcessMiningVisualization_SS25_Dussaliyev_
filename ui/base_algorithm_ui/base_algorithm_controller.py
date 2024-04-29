import streamlit as st
from abc import abstractmethod
from ui.base_ui.base_controller import BaseController
from utils.transformations import dataframe_to_cases_dict


class BaseAlgorithmController(BaseController):
    def __init__(self, views=None, model=None):

        self.model = model
        super().__init__(views)

    @abstractmethod
    def perform_mining(self) -> None:
        raise NotImplementedError("perform_mining() method not implemented")

    @abstractmethod
    def create_empty_model(self, log_data: tuple):
        raise NotImplementedError("create_empty_model() method not implemented")

    @abstractmethod
    def have_parameters_changed(self) -> bool:
        raise NotImplementedError("have_parameters_changed() method not implemented")

    def transform_df_to_log(self, df, **selected_columns) -> tuple:
        # TODO: implement this  method using a df transformation model
        return (dataframe_to_cases_dict(df, **selected_columns),)

    def read_values_from_session_state(self):
        super().read_values_from_session_state()
        if "df" in st.session_state and "selcted_columns" in st.session_state:
            log_data = self.transform_df_to_log(
                st.session_state.df, **st.session_state.selected_columns
            )
            st.session_state.model = self.create_empty_model(log_data)

        if "model" in st.session_state:
            self.model = st.session_state.model

    def run(self, view, pos):
        pass
