import streamlit as st
from ui.base_ui.base_view import BaseView
from components.buttons import navigation_button


class AlgorithmExplanationView(BaseView):

    def create_layout(self):
        super().create_layout()
        _, self.content_column, _ = st.columns([1, 6, 1])

    def display_algorithm_file(self, file_content):
        with self.content_column:
            st.markdown(file_content)

    def display_back_button(self):
        with self.content_column:
            navigation_button(
                "Back to Algorithm Page",
                route="Algorithm",
                type="secondary",
                use_container_width=True,
            )
