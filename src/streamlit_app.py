import streamlit as st
from ui.home_ui.home_controller import HomeController
from ui.column_selection_ui.column_selection_controller import ColumnSelectionController
from ui.export_ui.export_controller import ExportController
from ui.algorithm_explanation_ui.algorithm_explanation_controller import (
    AlgorithmExplanationController,
)
from components.theme_manager import theme_toggle

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

# Define theme colors
if st.session_state.theme == "dark":
    bg_color = "#0e1117"
    text_color = "#fafafa"
    control_bg = "#262730"
    input_bg = "#262730"
else:
    bg_color = "#ffffff"
    text_color = "#1a202c"
    control_bg = "#f0f2f6"
    input_bg = "#f0f2f6"  # Light background for inputs in light theme

# Add global CSS for theming and fixes
theme_css = f"""
<style>
    /* Fix for title overlapping with top interface */
    .block-container {{
        padding-top: 3rem !important;
    }}
    
    /* Additional space for titles */
    section.main h1:first-child {{
        margin-top: -2rem !important;
    }}
    
    /* Fix for streamlit components positioning */
    .stApp {{
        margin-top: 1rem;
        background-color: {bg_color} !important;
    }}
    
    /* Fix for main content background */
    [data-testid="stAppViewContainer"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    
    /* Make sidebar narrower and full height */
    [data-testid="stSidebar"] {{
        width: 18rem !important;
        min-width: 18rem !important;
        background-color: {control_bg} !important;
        height: 100vh !important;
        position: fixed !important;
        overflow-y: auto !important;
    }}
    
    /* Ensure main content area is properly positioned with fixed sidebar */
    [data-testid="stAppViewContainer"] > .main {{
        margin-left: 18rem !important;
    }}
    
    /* When sidebar is collapsed, reset main content margin */
    section[data-testid="stSidebar"][aria-expanded="false"] ~ .main {{
        margin-left: 0 !important;
    }}
    
    /* Adjust sidebar padding */
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }}
    
    /* Fix sidebar toggle button position and appearance */
    button[kind="headerNoPadding"],
    [data-testid="baseButton-headerNoPadding"] {{
        background-color: {control_bg} !important;
        color: {text_color} !important;
        border: 1px solid rgba(49, 51, 63, 0.2) !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: absolute !important;
        right: -18px !important; /* Move button more to the right */
        top: 50% !important;
        transform: translateY(-50%) !important;
        z-index: 100 !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }}
    
    /* Change sidebar toggle button icon */
    button[kind="headerNoPadding"] svg,
    [data-testid="baseButton-headerNoPadding"] svg {{
        display: none !important; /* Hide the default icon */
    }}
    
    /* Create custom icons using ::before for different states */
    [data-testid="baseButton-headerNoPadding"]::before {{
        content: "◀" !important; /* Left arrow when sidebar is expanded */
        font-size: 18px !important;
        font-weight: bold !important;
    }}
    
    /* When collapsed, the button moves to the right edge */
    section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="baseButton-headerNoPadding"]::before {{
        content: "▶" !important; /* Right arrow when sidebar is collapsed */
    }}
    
    /* Fix for all sidebar text */
    [data-testid="stSidebar"] * {{
        color: {text_color} !important;
    }}
    
    /* Fix for form elements with black background */
    div[data-baseweb="select"] {{
        background-color: {input_bg} !important;
    }}
    
    div[data-baseweb="select"] input, 
    div[data-baseweb="select"] [data-testid="stSelectbox"] {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
    }}
    
    /* Remove white overlay in dropdowns */
    div[data-baseweb="select"] div[data-testid="stMarkdownContainer"] {{
        background-color: transparent !important;
    }}
    
    /* Fix white space in dropdown */
    div[data-baseweb="select"] > div {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
    }}
    
    /* Dropdown arrow */
    div[data-baseweb="select"] svg {{
        color: {text_color} !important;
    }}
    
    /* Selected dropdown text */
    div[data-baseweb="select"] span {{
        color: {text_color} !important;
        background-color: transparent !important;
    }}
    
    /* Ensure dropdown options are visible */
    div[role="listbox"] {{
        background-color: {input_bg} !important;
    }}
    
    div[role="listbox"] div[role="option"] {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
    }}
    
    /* Ensure slider and number inputs have correct background */
    div[data-testid="stSlider"] {{
        background-color: transparent !important;
    }}
    
    input[type="number"] {{
        background-color: {input_bg} !important;
        color: {text_color} !important;
    }}
    
    /* Theme toggle buttons styling */
    .stButton > button {{
        height: 40px !important;
        min-width: 100px !important;
    }}
    
    /* Primary buttons styling */
    .stButton > button[data-testid="baseButton-primary"] {{
        background-color: #4b5eff !important;
        color: white !important;
    }}
</style>
"""

st.markdown(theme_css, unsafe_allow_html=True)

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
