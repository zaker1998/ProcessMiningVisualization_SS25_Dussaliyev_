from abc import ABC, abstractmethod
from views.ViewInterface import ViewInterface
import streamlit as st
from graphs.visualization.base_graph import BaseGraph
from components.interactiveGraph import interactiveGraph
from components.buttons import home_button, to_home, navigation_button
from time import time
from exceptions.graph_exceptions import InvalidNodeNameException


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
                to_home("Home")
                st.rerun()
            self.controller.set_model(st.session_state.model)
        else:
            if (
                "df" not in st.session_state
                or "time_column" not in st.session_state
                or "case_column" not in st.session_state
                or "activity_column" not in st.session_state
            ):
                to_home("Home")
            start = time()
            self.controller.create_model(
                st.session_state.df,
                st.session_state.time_column,
                st.session_state.activity_column,
                st.session_state.case_column,
            )
            end = time()
            print("Time to create model:", end - start)

            del st.session_state.df
            st.session_state.model = self.controller.get_model()

    def render(self):
        self.read_values_from_session_state()
        self.initialize_values()

        from config import docs_path_mappings

        if st.session_state.algorithm not in docs_path_mappings:
            st.title(self.get_page_title())

        else:
            title_column, button_column = st.columns([3, 1])
            with title_column:
                st.title(self.get_page_title())
            with button_column:
                navigation_button(
                    "Algorithm Explanation",
                    "Documentation",
                    use_container_width=True,
                )
        with st.sidebar:
            self.render_sidebar()
        start = time()
        try:
            self.controller.perform_mining()
        except InvalidNodeNameException as ex:
            # TODO: add logging
            print(ex)
            st.session_state.error = (
                ex.message
                + "\n Please check the input data. The string'___' is not allowed in node names."
            )
            to_home()

        end = time()
        print("Time to perform mining:", end - start)

        graph_container = st.container(border=True)

        button_container = st.container()

        self.node_info_container = st.container()
        with graph_container:
            interactiveGraph(
                self.controller.get_graph(), onNodeClick=self.display_node_info
            )
        with button_container:
            columns = st.columns([1, 1, 1])
            with columns[0]:
                home_button("Back", use_container_width=True)
            with columns[2]:
                navigation_button(
                    "Export",
                    "Export",
                    use_container_width=True,
                )

    def display_node_info(self, node_name: str, node_description: str):
        with self.node_info_container:
            with st.expander(f"Node: {node_name}"):
                for line in node_description.split("\n"):
                    st.write(line)
