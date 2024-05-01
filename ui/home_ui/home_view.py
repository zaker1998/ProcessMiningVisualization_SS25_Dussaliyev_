import streamlit as st
from ui.base_ui.base_view import BaseView
from config import algorithm_mappings
from components.buttons import navigation_button


class HomeView(BaseView):

    def create_layout(self):
        super().create_layout()
        _, self.content_column, _ = st.columns([1, 3, 1])

    def display_intro(self):
        with self.content_column:
            st.title("Welcome to the Process Mining Tool")
            st.write(
                "This tool is designed to help you visualize the dependencies between activities in your process logs."
            )
            st.write("To get started, upload a CSV file containing your process logs.")

    def display_file_upload(self):
        with self.content_column:
            self.file = st.file_uploader(
                "Upload a file",
                type=["csv", "pickle"],
                accept_multiple_files=False,
            )

        if self.file:
            self.controller.process_file(self.file)

    def display_model_import(self, model):
        with self.content_column:
            algorithm_col, _, button_column = st.columns([2, 2, 1])
            with algorithm_col:
                selection = st.selectbox(
                    "Mining Algorthm", list(algorithm_mappings.keys())
                )

            with button_column:
                st.write("")
                navigation_button(
                    label="Import Model",
                    route="Algorithm",
                    use_container_width=True,
                    beforeNavigate=self.controller.set_model_and_algorithm,
                    args=(model, algorithm_mappings[selection]),
                )

    def display_df_import(self, detected_delimiter):
        with self.content_column:
            delimiter_col, _, button_column = st.columns([1, 3, 1])

            with delimiter_col:
                delimiter = st.text_input(
                    "Delimiter", value=detected_delimiter, key="delimiter", max_chars=1
                )

            with button_column:
                st.write("")
                navigation_button(
                    label="Mine from File",
                    route="ColumnSelection",
                    use_container_width=True,
                    beforeNavigate=self.controller.set_df,
                    args=(self.file, delimiter),
                )
