from abc import ABC, abstractmethod
from views.ViewInterface import ViewInterface
import streamlit as st
from graphs.visualization.base_graph import BaseGraph


class AlgorithmViewInterface(ViewInterface, ABC):

    def __init__(self):
        self.sliders = {}
        super().__init__()

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

        st.title(self.get_page_title())

        self.render_sliders()
        graph = self.perform_mining(st.session_state.cases)

        graph_container = st.container(border=True)
        with graph_container:
            st.graphviz_chart(graph.get_graphviz_string())

    def add_slider(
        self,
        min: int | float,
        max: int | float,
        value: int | float,
        steps: float | int,
        label: str,
        key: str,
    ) -> None:
        self.sliders[key] = st.sidebar.slider(
            label, min, max, value=value, step=steps, key=key
        )

    def get_slider_value(self, key: str) -> int:
        return self.sliders[key]
