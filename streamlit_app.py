"""
Main Streamlit application for the Process Mining Tool.
This module serves as the entry point for the application and handles routing between different pages.
"""

import streamlit as st
from typing import Dict, Type

# Import controllers
from ui.home_ui.home_controller import HomeController
from ui.column_selection_ui.column_selection_controller import ColumnSelectionController
from ui.export_ui.export_controller import ExportController
from ui.algorithm_explanation_ui.algorithm_explanation_controller import (
    AlgorithmExplanationController,
)
from config import algorithm_routes

# Configure page settings
st.set_page_config(
    page_title="Process Mining Tool",
    page_icon=":bar_chart:",
    layout="wide",
)

# Add global CSS for consistent styling
st.markdown("""
<style>
    /* Fix for title overlapping with top interface */
    .block-container {
        padding-top: 3rem !important;
    }
    
    /* Additional space for titles */
    section.main h1:first-child {
        margin-top: 1rem !important;
    }
    
    /* Fix for streamlit components positioning */
    .stApp {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Page routing logic
PAGE_ROUTING: Dict[str, Type] = {
    "Home": HomeController,
    "ColumnSelection": ColumnSelectionController,
    "Export": ExportController,
    "Documentation": AlgorithmExplanationController,
}

# Handle page routing
if st.session_state.page == "Algorithm":
    algorithm_routes[st.session_state.algorithm]().start()
else:
    PAGE_ROUTING[st.session_state.page]().start()
