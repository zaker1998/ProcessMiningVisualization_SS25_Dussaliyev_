import streamlit as st
from ui.column_selection_ui.base_column_selection_view import BaseColumnSelectionView


class BaseColumnSelectionViewTemplate(BaseColumnSelectionView):
    """Standard view for the column selection."""

    def __init__(self):
        """Initializes the standard column selection view. It sets the needed columns and column styles."""
        self.needed_columns = []
        # e.g.["time_column", "case_column", "activity_column"]
        self.column_styles = dict()
        # e.g.{
        #    "time_column": "background-color: #FF705B",
        #    "case_column": "background-color: #629AFF",
        #    "activity_column": "background-color: #57B868",
        # }

        raise NotImplementedError(
            "Method __init__ must be implemented in the child class"
        )

    def get_needed_columns(self) -> list[str]:
        """Returns the needed columns for the algorithm. This will be used to display the column selection options.

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
        raise NotImplementedError(
            "Method render_column_selections must be implemented in the child class"
        )
