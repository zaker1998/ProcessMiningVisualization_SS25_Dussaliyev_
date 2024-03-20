from abc import ABC, abstractmethod
from views.ViewInterface import ViewInterface
import streamlit as st
from graphs.visualization.base_graph import BaseGraph


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
    def get_page_title(self) -> str:
        return "Algorithm View Interface"

    def render(self):
        if "cases" not in st.session_state:
            st.session_state.page = "Home"
            st.rerun()

        self.initialize_values()

        st.title(self.get_page_title())

        self.render_sliders()
        self.graph = self.perform_mining(st.session_state.cases)

        graph_container = st.container(border=True)
        with graph_container:
            st.graphviz_chart(self.graph.get_graphviz_string())

        def back_to_home():
            st.session_state.page = "Home"

        st.button("Back", on_click=self.back_to_home, type="secondary")
        st.button("Export", on_click=self.to_export_view, type="secondary")

    def back_to_home(self):
        st.session_state.page = "Home"

    def to_export_view(self):
        st.session_state.page = "Export"
        st.session_state.graph = self.graph

    def add_slider(
        self,
        min: int | float,
        max: int | float,
        steps: float | int,
        label: str,
        key: str,
    ) -> None:
        # stored values in session state lost after switching to another page
        st.sidebar.slider(label, min, max, step=steps, key=key)

    def get_slider_value(self, key: str) -> int:
        return st.session_state[key]
