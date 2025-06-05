import streamlit as st
from ui.home_ui.home_controller import HomeController
from ui.column_selection_ui.column_selection_controller import ColumnSelectionController
from ui.export_ui.export_controller import ExportController
from ui.algorithm_explanation_ui.algorithm_explanation_controller import (
    AlgorithmExplanationController,
)
from components.theme_manager import theme_toggle
from components.styles.theme_manager import apply_theme

from config import algorithm_routes


st.set_page_config(
    page_title="Process Mining Tool",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/MLUX-University-of-Vienna/ProcessMiningVisualization_SS24_Frauenberger/issues",
        "Report a bug": "https://github.com/MLUX-University-of-Vienna/ProcessMiningVisualization_SS24_Frauenberger/issues/new",
        "About": "Process Mining Visualization Tool v0.2.0"
    }
)

# Initialize session state variables if they don't exist
if "theme" not in st.session_state:
    st.session_state.theme = "light"
    
if "execution_times" not in st.session_state:
    st.session_state.execution_times = {}

# Apply the theme styling
apply_theme()

# Use our custom theme toggle in sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    # Use our custom theme toggle component
    theme_toggle()
    
    # Show execution times if available
    if st.session_state.execution_times:
        st.subheader("Performance Metrics")
        for func_name, exec_time in st.session_state.execution_times.items():
            st.text(f"{func_name}: {exec_time:.2f}s")
    
    # Version info at bottom of sidebar
    st.sidebar.info("Process Mining Tool v0.2.0")

# Initialize page state if not exists
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Navigation
if st.session_state.page == "Home":
    HomeController().start()
elif st.session_state.page == "Algorithm":
    algorithm_routes[st.session_state.algorithm]().start()
elif st.session_state.page == "ColumnSelection":
    ColumnSelectionController().start()
elif st.session_state.page == "Export":
    ExportController().start()
elif st.session_state.page == "Documentation":
    AlgorithmExplanationController().start()
