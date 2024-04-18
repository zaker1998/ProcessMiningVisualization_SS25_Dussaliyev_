from views.ViewInterface import ViewInterface
import streamlit as st
from components.buttons import navigation_button, navigate_to, to_home
from config import docs_path_mappings


class AlgorithmDocView(ViewInterface):

    def render(self):
        if "algorithm" not in st.session_state:
            st.session_state.error = "Algorithm not selected"
            to_home()

        if st.session_state.algorithm not in docs_path_mappings:
            st.session_state.error = "Algorithm does not have documentation"
            navigate_to("Algorithm")
        _, page_column, _ = st.columns([1, 6, 1])
        with page_column:
            navigation_button(
                "Back to Algorithm Page",
                route="Algorithm",
                type="secondary",
                use_container_width=True,
            )
            with open(docs_path_mappings[st.session_state.algorithm], "r") as file:
                st.markdown(file.read())
