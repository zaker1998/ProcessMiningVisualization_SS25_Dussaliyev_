from abc import ABC, abstractmethod
from views.ViewInterface import ViewInterface
import streamlit as st
from graphs.visualization.base_graph import BaseGraph
from components.interactiveGraph import interactiveGraph


class AlgorithmViewInterface(ViewInterface, ABC):

    controller = None

    @abstractmethod
    def initialize_values(self):
        raise NotImplementedError("initialize_values() method not implemented")

    @abstractmethod
    def is_correct_model_type(self, model) -> bool:
        raise NotImplementedError("is_correct_model_type() method not implemented")

    @abstractmethod
    def render_sidebar(self):
        raise NotImplementedError("render_sidebar() method not implemented")

    @abstractmethod
    def get_page_title(self) -> str:
        return "Algorithm View Interface"

    def read_values_from_session_state(self):
        if "model" in st.session_state:
            if not self.is_correct_model_type(st.session_state.model):
                st.session_state.error = "Invalid model type"
                self.navigte_to("Home", True)
                st.rerun()
            self.controller.set_model(st.session_state.model)
        else:
            if (
                "df" not in st.session_state
                or "time_column" not in st.session_state
                or "case_column" not in st.session_state
                or "activity_column" not in st.session_state
            ):
                self.navigte_to("Home", True)

            self.controller.create_model(
                st.session_state.df,
                st.session_state.time_column,
                st.session_state.activity_column,
                st.session_state.case_column,
            )

            del st.session_state.df
            st.session_state.model = self.controller.get_model()

    def render(self):
        self.read_values_from_session_state()
        self.initialize_values()

        st.title(self.get_page_title())
        with st.sidebar:
            self.render_sidebar()

        self.controller.perform_mining()

        interactiveGraph(self.controller.get_graph())

        columns = st.columns([1, 1, 1])
        with columns[0]:
            st.button(
                "Back",
                on_click=self.navigte_to,
                args=("Home", True),
                type="secondary",
                use_container_width=True,
            )
        with columns[2]:
            st.button(
                "Export",
                on_click=self.navigte_to,
                args=("Export",),
                type="primary",
                use_container_width=True,
            )

    def clear(self):
        return
