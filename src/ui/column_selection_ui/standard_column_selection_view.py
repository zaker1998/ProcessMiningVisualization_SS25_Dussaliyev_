import streamlit as st
from ui.column_selection_ui.base_column_selection_view import BaseColumnSelectionView
from ui.base_ui.base_view import BaseView


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

        # Get current theme to style the card appropriately
        current_theme = st.session_state.get("theme", "light")
        
        if current_theme == "dark":
            card_bg = "#2d3748"
            text_color = "#ffffff"
        else:
            card_bg = "#f7fafc"
            text_color = "#2d3748"

        # Add a helpful card at the top with theme-aware styling
        st.markdown(f"""
        <div style="background-color: {card_bg}; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e2e8f0;">
            <h3 style="color: {text_color};">📋 Column Selection</h3>
            <p style="color: {text_color};">Please map your data columns to the required process mining fields:</p>
            <ul style="color: {text_color};">
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
