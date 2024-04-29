import streamlit as st
from abc import abstractmethod
from ui.base_ui.base_controller import BaseController
from utils.transformations import dataframe_to_cases_dict


class BaseAlgorithmController(BaseController):
    def __init__(self, views=None, model=None):

        self.mining_model = model
        super().__init__(views)

    @abstractmethod
    def perform_mining(self) -> None:
        raise NotImplementedError("perform_mining() method not implemented")

    @abstractmethod
    def create_empty_model(self, *log_data):
        raise NotImplementedError("create_empty_model() method not implemented")

    @abstractmethod
    def have_parameters_changed(self) -> bool:
        raise NotImplementedError("have_parameters_changed() method not implemented")

    @abstractmethod
    def is_correct_model_type(self, model) -> bool:
        raise NotImplementedError("is_correct_model_type() method not implemented")

    def transform_df_to_log(self, df, **selected_columns) -> tuple:
        # TODO: implement this  method using a df transformation model
        cases_dict = dataframe_to_cases_dict(df, **selected_columns)
        return (cases_dict,)

    def process_session_state(self):
        super().read_values_from_session_state()
        if "model" in st.session_state:
            if not self.is_correct_model_type(st.session_state.model):
                st.session_state.error = "Invalid model type."
                to_home("Home")
                st.rerun()
            self.mining_model = st.session_state.model
        else:
            if (
                "df" not in st.session_state
                or "selected_columns" not in st.session_state
            ):
                st.session_state.error = "A DataFrame and selected columns must be provided to create a model."
                to_home("Home")
                st.rerun()

            log_data = self.transform_df_to_log(
                st.session_state.df, **st.session_state.selected_columns
            )
            st.session_state.model = self.create_empty_model(*log_data)
            self.mining_model = st.session_state.model

    def run(self, view, pos):
        if self.have_parameters_changed():
            self.perform_mining()

        view.display_sidebar()
        view.display_graph(self.model.get_graph())
        view.display_navigation_buttons()
