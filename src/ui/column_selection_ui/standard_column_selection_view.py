import streamlit as st
from ui.column_selection_ui.base_column_selection_view import BaseColumnSelectionView


class StandardColumnSelectionView(BaseColumnSelectionView):
    """Standard view for the column selection. It contains the 'time_column', 'case_column' and 'activity_column'."""

    def __init__(self):
        """Initializes the standard column selection view. It sets the needed columns and column styles."""
        super().__init__()

        self.needed_columns.extend(["time_column", "case_column", "activity_column"])

        self.column_styles.update(
            {
                "time_column": "background-color: #FF705B",
                "case_column": "background-color: #629AFF",
                "activity_column": "background-color: #57B868",
            }
        )

    def render_column_selections(self, columns: list[str]):
        """Renders the column selection options."""

        # Add a helpful card at the top
        st.markdown("""
        <div style="background-color: #2d3748; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="color: #ffffff;">📋 Column Selection</h3>
            <p style="color: #ffffff;">Please map your data columns to the required process mining fields:</p>
            <ul style="color: #ffffff;">
                <li><strong style="color: #FF705B;">Time column</strong>: Contains timestamps of events</li>
                <li><strong style="color: #629AFF;">Case column</strong>: Identifies the process instance</li>
                <li><strong style="color: #57B868;">Activity column</strong>: Describes the activity performed</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        time_col, case_col, activity_col = st.columns(3)
        with time_col:
            st.selectbox(
                "Select the :red[time column] ⏱️",
                columns,
                key=self.needed_columns[0],
                index=None,
                help="This column should contain timestamps indicating when each activity occurred"
            )

        with case_col:
            st.selectbox(
                "Select the :blue[case column] 📁",
                columns,
                key=self.needed_columns[1],
                index=None,
                help="This column should contain identifiers for each process instance"
            )

        with activity_col:
            st.selectbox(
                "Select the :green[activity column] 🔧",
                columns,
                key=self.needed_columns[2],
                index=None,
                help="This column should contain the names of activities performed in the process"
            )
