from views.ViewInterface import ViewInterface
import streamlit as st
import os
from utils.transformations import dataframe_to_cases_list
from utils.io import read_file
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

            file = st.file_uploader(
                "Upload a file",
                type=["csv", "pickle"],
                accept_multiple_files=False,
                key="file_uploader",
            )

            if file:
                self.processed_file = read_file(file)
                if file.name.endswith(".csv"):
                    self.render_df_import()
                elif file.name.endswith(".pickle"):
                    self.render_model_import()

    def render_model_import(self):
        selection = st.selectbox("Mining Algorthm", list(algorithm_mappings.keys()))

        if st.button("Import Model", type="primary"):
            st.session_state.algorithm = algorithm_mappings[selection]
            st.session_state.model = self.processed_file
            self.navigte_to("Algorithm")
            st.rerun()

    def render_df_import(self):
        if st.button("Mine from File", type="primary"):
            st.session_state.df = self.processed_file
            self.navigte_to("ColumnSelection")
            st.rerun()

    def clear(self):
        return
