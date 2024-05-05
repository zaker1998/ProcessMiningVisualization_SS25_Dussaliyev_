import streamlit as st
from abc import abstractmethod
from ui.base_ui.base_controller import BaseController
from transformations.dataframe_transformations import DataframeTransformations
from components.buttons import to_home
from exceptions.graph_exceptions import InvalidNodeNameException, GraphException

from time import time


class BaseAlgorithmController(BaseController):
    def __init__(self, views=None, mining_model_class=None):

        self.mining_model = None
        self.dataframe_transformations = DataframeTransformations()
        self.mining_model_class = mining_model_class
        super().__init__(views)

    @abstractmethod
    def perform_mining(self) -> None:
        raise NotImplementedError("perform_mining() method not implemented")

    @abstractmethod
    def process_algorithm_parameters(self):
        raise NotImplementedError(
            "process_algorithm_parameters() method not implemented"
        )

    @abstractmethod
    def have_parameters_changed(self) -> bool:
        raise NotImplementedError("have_parameters_changed() method not implemented")

    @abstractmethod
    def get_sidebar_values(self) -> dict[str, any]:
        raise NotImplementedError("get_sidebar_values() method not implemented")

    def is_correct_model_type(self, model) -> bool:
        return isinstance(model, self.mining_model_class)

    def create_empty_model(self, *log_data):
        return self.mining_model_class.create_mining_instance(*log_data)

    def transform_df_to_log(self, df, **selected_columns) -> tuple:
        self.dataframe_transformations.set_dataframe(df)
        return (
            self.dataframe_transformations.dataframe_to_cases_dict(**selected_columns),
        )

    def process_session_state(self):
        super().process_session_state()
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
                to_home()
                st.rerun()
            start = time()
            log_data = self.transform_df_to_log(
                st.session_state.df, **st.session_state.selected_columns
            )
            st.session_state.model = self.create_empty_model(*log_data)
            end = time()
            print("Time to create model:", end - start)
            self.mining_model = st.session_state.model

            del st.session_state.df
            del st.session_state.selected_columns

    def run(self, view, pos):
        self.process_algorithm_parameters()
        view.display_sidebar(self.get_sidebar_values())
        view.display_back_button()
        view.display_export_button(disabled=True)
        if self.have_parameters_changed() or self.mining_model.get_graph() is None:
            start = time()
            try:
                view.display_loading_spinner("Mining...", self.perform_mining)
            except InvalidNodeNameException as ex:
                # TODO: add logging
                print(ex)
                st.session_state.error = (
                    ex.message
                    + "\n Please check the input data. The string '___' is not allowed in node names."
                )
                to_home()
                st.rerun()
            except GraphException as ex:
                # TODO: add logging
                print(ex)
                st.warning(
                    "Do not change the parameters while mining. This will cause an error. Wait until the mining is finished."
                )

            end = time()
            print("Time to perform mining:", end - start)
        view.display_graph(self.mining_model.get_graph())
        view.display_export_button(disabled=False)
