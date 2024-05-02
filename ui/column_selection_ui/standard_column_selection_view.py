import streamlit as st
from ui.column_selection_ui.base_column_selection_view import BaseColumnSelectionView


class StandardColumnSelectionView(BaseColumnSelectionView):
    def __init__(self):
        self.needed_columns = ["time_column", "case_column", "activity_column"]
        self.column_styles = {
            "time_column": "background-color: #FF705B",
            "case_column": "background-color: #629AFF",
            "activity_column": "background-color: #57B868",
        }

    def get_needed_columns(self) -> list[str]:
        return self.needed_columns

    def get_column_styles(self) -> dict[str, str]:
        return self.column_styles

    def render_column_selections(self, columns: list[str]):

        time_col, case_col, activity_col = st.columns(3)
        with time_col:
            st.selectbox(
                "Select the :red[time column]",
                columns,
                key=self.needed_columns[0],
                index=None,
            )

        with case_col:
            st.selectbox(
                "Select the :blue[case column]",
                columns,
                key=self.needed_columns[1],
                index=None,
            )

        with activity_col:
            st.selectbox(
                "Select the :green[activity column]",
                columns,
                key=self.needed_columns[2],
                index=None,
            )
