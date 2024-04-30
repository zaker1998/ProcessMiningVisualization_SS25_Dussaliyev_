import streamlit as st
from abc import abstractmethod
from ui.base_ui.base_controller import BaseController
from utils.transformations import dataframe_to_cases_dict
from components.buttons import to_home
from exceptions.graph_exceptions import InvalidNodeNameException, GraphException
from time import time


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

    @abstractmethod
    def get_sidebar_values(self) -> dict[str, any]:
        raise NotImplementedError("get_sidebar_values() method not implemented")

    def transform_df_to_log(self, df, **selected_columns) -> tuple:
        # TODO: implement this  method using a df transformation model
        cases_dict = dataframe_to_cases_dict(df, **selected_columns)
        return (cases_dict,)

    def process_session_state(self):
        super().process_session_state()
        if "model" in st.session_state:
            if not self.is_correct_model_type(st.session_state.model):
                st.session_state.error = "Invalid model type."
                to_home("Home")
                st.rerun()
            self.mining_model = st.session_state.model
        else:
            # TODO: revert back to store selcted columns ina dict in session state
            if (
                "df" not in st.session_state
                # or "selected_columns" not in st.session_state
                or "time_column" not in st.session_state
                or "case_column" not in st.session_state
                or "activity_column" not in st.session_state
            ):
                st.session_state.error = "A DataFrame and selected columns must be provided to create a model."
                to_home()
                st.rerun()
            start = time()
            log_data = self.transform_df_to_log(
                st.session_state.df,
                timeLabel=st.session_state.time_column,
                eventLabel=st.session_state.activity_column,
                caseLabel=st.session_state.case_column,  # **st.session_state.selected_columns
            )
            st.session_state.model = self.create_empty_model(*log_data)
            end = time()
            print("Time to create model:", end - start)
            self.mining_model = st.session_state.model

            del st.session_state.df
            del st.session_state.time_column
            del st.session_state.activity_column
            del st.session_state.case_column
            # del st.session_state.selected_columns

    def run(self, view, pos):
        view.create_layout()

        view.display_sidebar(self.get_sidebar_values())
        view.display_back_button()
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
        view.display_export_button()
