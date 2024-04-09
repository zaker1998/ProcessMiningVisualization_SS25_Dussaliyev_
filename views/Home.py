from views.ViewInterface import ViewInterface
import streamlit as st
import os
from utils.transformations import dataframe_to_cases_list
from utils.io import read_file, detect_delimiter
from config import algorithm_mappings


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
            if st.button("Import Model", type="primary", use_container_width=True):
                st.session_state.algorithm = algorithm_mappings[selection]
                st.session_state.model = model
                self.navigte_to("Algorithm")
                st.rerun()

    def render_df_import(self):
        detected_delimiter = ""
        try:
            detected_delimiter = detect_delimiter(self.file)
        except Exception as e:
            print(e)

        delimiter_col, _, button_column = st.columns([1, 3, 1])

        with delimiter_col:
            delimiter = st.text_input(
                "Delimiter", value=detected_delimiter, key="delimiter", max_chars=1
            )

        with button_column:
            st.write("")
            if st.button("Mine from File", type="primary", use_container_width=True):
                if delimiter == "":
                    st.session_state.error = "Please enter a delimiter"
                    st.rerun()
                    return
                st.session_state.df = read_file(self.file, delimiter=delimiter)
                self.navigte_to("ColumnSelection")
                st.rerun()

    def clear(self):
        return
