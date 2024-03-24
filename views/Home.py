from views.ViewInterface import ViewInterface
import streamlit as st
import os
from utils.transformations import dataframe_to_cases_list
from utils.io import read_file


class Home(ViewInterface):
    def render(self):
        st.title("Welcome to the Process Mining Tool")
        st.write(
            "This tool is designed to help you visualize the dependencies between activities in your process logs."
        )
        st.write("To get started, upload a CSV file containing your process logs.")

        file = st.file_uploader(
            "Upload a file",
            type=["csv"],
            accept_multiple_files=False,
        )

        if file:
            df = read_file(file)
            st.session_state.df = df
            self.navigte_to("ColumnSelection")
            st.rerun()

    def clear(self):
        return
