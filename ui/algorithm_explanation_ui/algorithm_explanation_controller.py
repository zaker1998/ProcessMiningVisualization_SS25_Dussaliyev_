import streamlit as st
from ui.base_ui.base_controller import BaseController
from components.buttons import navigate_to, to_home
from config import docs_path_mappings


class AlgorithmExplanationController(BaseController):

    def __init__(self, views=None):
        if views is None:
            from ui.algorithm_explanation_ui.algorithm_explanation_view import (
                AlgorithmExplanationView,
            )

            views = [AlgorithmExplanationView()]
        super().__init__(views)

    def get_page_title(self) -> str:
        return ""

    def process_session_state(self):
        if "algorithm" not in st.session_state:
            st.session_state.error = "Algorithm not selected"
            to_home()

        if st.session_state.algorithm not in docs_path_mappings:
            st.session_state.error = "Algorithm does not have documentation"
            navigate_to("Algorithm")

        self.file_path = docs_path_mappings[st.session_state.algorithm]

    def read_algorithm_file(self) -> str:
        # TODO: move io logic to a model
        with open(self.file_path, "r") as file:
            file_content = file.read()

        return file_content

    def run(self, selected_view, index):
        self.selected_view = selected_view
        selected_view.display_back_button()
        file_content = self.read_algorithm_file()
        selected_view.display_algorithm_file(file_content)
