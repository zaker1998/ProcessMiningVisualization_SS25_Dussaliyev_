from views.ViewInterface import ViewInterface
import streamlit as st
import os
from utils.transformations import dataframe_to_cases_list
from utils.io import read_file, detect_delimiter
from config import algorithm_mappings
from components.buttons import navigation_button


class Home(ViewInterface):
    def render(self):
        _, col, _ = st.columns([1, 3, 1])
        with col:
            st.title("Welcome to the Process Mining Tool")
            st.write(
                "This tool is designed to help you visualize the dependencies between activities in your process logs."
            )
            st.write("To get started, upload a CSV file containing your process logs.")

            self.file = st.file_uploader(
                "Upload a file",
                type=["csv", "pickle"],
                accept_multiple_files=False,
            )

            if self.file:
                if self.file.name.endswith(".csv"):
                    self.render_df_import()
                elif self.file.name.endswith(".pickle"):
                    self.render_model_import()

    def render_model_import(self):
        model = read_file(self.file)
        algorithm_col, _, button_column = st.columns([2, 2, 1])
        with algorithm_col:
            selection = st.selectbox("Mining Algorthm", list(algorithm_mappings.keys()))

        with button_column:
            st.write("")
            navigation_button(
                label="Import Model",
                route="Algorithm",
                use_container_width=True,
                beforeNavigate=self.__set_model_and_algorithm,
                args=(model, algorithm_mappings[selection]),
            )

    def render_df_import(self):
        detected_delimiter = ""
        try:
            detected_delimiter = detect_delimiter(self.file)
        except Exception as e:
            # TODO: use logging
            print(e)

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
                beforeNavigate=self.__set_df,
                args=(self.file, delimiter),
            )

    def __set_model_and_algorithm(self, model, algorithm):
        st.session_state.model = model
        st.session_state.algorithm = algorithm

    def __set_df(self, file, delimiter):
        if delimiter == "":
            st.session_state.error = "Please enter a delimiter"
            # change routing to home
            st.session_state.page = "Home"
            return
        st.session_state.df = read_file(file, delimiter=delimiter)
