import streamlit as st
from ui.column_selection_ui.base_column_selection_view import BaseColumnSelectionView


class StandardColumnSelectionView(BaseColumnSelectionView):
    """Standard view for the column selection. It contains the 'time_column', 'case_column' and 'activity_column'."""

    def __init__(self):
        """Initializes the standard column selection view. It sets the needed columns and column styles."""
        self.needed_columns = ["time_column", "case_column", "activity_column"]
        self.column_styles = {
            "time_column": "background-color: #FF705B",
            "case_column": "background-color: #629AFF",
            "activity_column": "background-color: #57B868",
        }

    def get_needed_columns(self) -> list[str]:
        """Returns the needed columns for the algorithm. This will be used to display the column selection options.
        The columns are 'time_column', 'case_column' and 'activity_column'.

        Returns
        -------
        list[str]
            The needed columns for the algorithm.
        """
        return self.needed_columns

    def get_column_styles(self) -> dict[str, str]:
        """Returns the styles for the columns. This will be used to style the column selection options.
        The 'time_column' is styled with a red background, the 'case_column' with a blue background and the 'activity_column' with a green background.

        Returns
        -------
        dict[str, str]
            The styles for the columns.
        """
        return self.column_styles

    def render_column_selections(self, columns: list[str]):
        """Renders the column selection options.

        Parameters
        ----------
        columns : list[str]
            The names of the needed columns
        """

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
