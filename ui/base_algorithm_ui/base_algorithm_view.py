import streamlit as st
from ui.base_ui.base_view import BaseView
from components.buttons import home_button, navigation_button
from components.interactiveGraph import interactiveGraph
from abc import abstractmethod


class BaseAlgorithmView(BaseView):
    graph_height = 600

    def create_layout(self):
        graph_wrapper_container = st.container(
            border=True, height=self.graph_height + 40
        )  # add 40 to height to account for padding
        with graph_wrapper_container:
            self.graph_container = st.empty()
        button_container = st.container()
        self.node_data_container = st.container()
        with button_container:
            self.back_button_column, _, export_button_column = st.columns([1, 1, 1])

        with export_button_column:
            self.export_button_container = st.empty()

    @abstractmethod
    def render_sidebar(self, sidebar_values: dict[str, any]) -> None:
        raise NotImplementedError("render_sidebar() method not implemented")

    def display_sidebar(self, sidebar_values: dict[str, any]) -> None:
        with st.sidebar:
            self.render_sidebar(sidebar_values)

    def display_back_button(self) -> None:
        with self.back_button_column:
            home_button("Back", use_container_width=True)

    def display_export_button(self, disabled=False) -> None:
        with self.export_button_container:
            navigation_button(
                "Export",
                "Export",
                use_container_width=True,
                disabled=disabled,
                key="export_button-" + str(disabled),
            )

    def display_graph(self, graph) -> None:
        with self.graph_container:
            if graph is not None:
                interactiveGraph(
                    graph,
                    onNodeClick=self.display_node_info,
                    height=self.graph_height,
                )

    def display_loading_spinner(self, message: str, operation) -> None:
        with self.graph_container:
            with st.spinner(message):
                operation()

    def display_node_info(self, node_name: str, node_description: str) -> None:
        with self.node_data_container:
            with st.expander(f"Node: {node_name}"):
                for line in node_description.split("\n"):
                    st.write(line)

    def display_page_title(self, title) -> None:
        from config import docs_path_mappings

        if st.session_state.algorithm not in docs_path_mappings:
            st.title(title)

        else:
            title_column, button_column = st.columns([3, 1])
            with title_column:
                st.title(title)
            with button_column:
                navigation_button(
                    "Algorithm Explanation",
                    "Documentation",
                    use_container_width=True,
                )
