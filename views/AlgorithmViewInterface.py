from abc import ABC, abstractmethod
from views.ViewInterface import ViewInterface
import streamlit as st
from graphs.visualization.base_graph import BaseGraph
from utils.transformations import dataframe_to_cases_list


class AlgorithmViewInterface(ViewInterface, ABC):

    @abstractmethod
    def initialize_values(self):
        raise NotImplementedError("initialize_values() method not implemented")

    @abstractmethod
    def perform_mining(self, cases: list[list[str, ...]]) -> BaseGraph:
        raise NotImplementedError("perform_mining() method not implemented")

    @abstractmethod
    def render_sliders(self):
        raise NotImplementedError("render_sliders() method not implemented")

    @abstractmethod
    def clear(self):
        raise NotImplementedError("clear() method not implemented")

    @abstractmethod
    def get_page_title(self) -> str:
        return "Algorithm View Interface"

    def transform_df_to_cases(self):
        if (
            "df" not in st.session_state
            or "time_column" not in st.session_state
            or "case_column" not in st.session_state
            or "activity_column" not in st.session_state
        ):
            self.navigte_to("Home", True)
            return

        st.session_state.cases = dataframe_to_cases_list(
            st.session_state.df,
            st.session_state.time_column,
            st.session_state.case_column,
            st.session_state.activity_column,
        )

        del st.session_state.df

    def render(self):
        if "cases" not in st.session_state:
            self.transform_df_to_cases()

        self.initialize_values()

        st.title(self.get_page_title())
        with st.sidebar:
            self.render_sliders()

        self.graph = self.perform_mining(st.session_state.cases)

        graph_container = st.container(border=True)
        with graph_container:
            st.graphviz_chart(self.graph.get_graphviz_string())

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
                on_click=self.to_export_view,
                type="primary",
                use_container_width=True,
            )

    def to_export_view(self):
        self.navigte_to("Export")
        st.session_state.graph = self.graph

    def clear(self):
        del st.session_state.cases
        del st.session_state.algorithm
