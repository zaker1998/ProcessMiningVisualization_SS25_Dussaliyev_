import streamlit as st
from ui.column_selection_ui.standard_column_selection_view import (
    StandardColumnSelectionView,
)


class ExtendedColumnSelectionViewTemplate(StandardColumnSelectionView):
    """Standard view for the column selection."""

    def __init__(self):
        """Initializes the standard column selection view. It sets the needed columns and column styles."""
        super().__init__()

        # Add the needed columns and column styles here
        # self.needed_columns.append("additional_column")
        # self.column_styles["additional_column"] = "background-color: #FF705B"

    # OPTIONAL: Is defined in the parent class
    def get_needed_columns(self) -> list[str]:
        """Returns the needed columns for the algorithm. This will be used to display the column selection options.

        Returns
        -------
        list[str]
            The needed columns for the algorithm.
        """
        return self.needed_columns

    # OPTIONAL: Is defined in the parent class
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
        super().render_column_selections(columns)
        # Add the rendering of the additional column here
        # e.g.
        # additional_col = st.columns(1)
        # with additional_col:
        #     st.selectbox("Select the :blue[case column]",
        #        columns,
        #        key=self.needed_columns[3],
        #        index=None
        #     )
