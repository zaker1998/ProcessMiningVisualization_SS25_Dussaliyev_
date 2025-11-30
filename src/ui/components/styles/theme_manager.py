"""
Theme management for the application.
This module coordinates the application of different style components based on the current theme.
"""
import streamlit as st
from .base import get_layout_styles
from .sidebar import get_sidebar_styles, get_sidebar_toggle_styles
from .forms import get_form_styles
from .buttons import get_button_styles

def get_theme_colors(theme="light"):
    """
    Get the color palette for the specified theme.
    
    Parameters
    ----------
    theme : str
        The theme name, either "light" or "dark"
        
    Returns
    -------
    dict
        Dictionary containing color values for the theme
    """
    if theme == "dark":
        return {
            "bg_color": "#0e1117",
            "text_color": "#fafafa",
            "control_bg": "#262730",
            "input_bg": "#262730"
        }
    else:  # light theme
        return {
            "bg_color": "#ffffff",
            "text_color": "#1a202c",
            "control_bg": "#f0f2f6",
            "input_bg": "#f0f2f6"
        }

def apply_theme():
    """
    Apply the current theme to the application.
    
    Retrieves the current theme from session state and applies all relevant styles.
    
    Returns
    -------
    None
    """
    # Get current theme from session state
    current_theme = st.session_state.get("theme", "light")
    
    # Get theme colors
    colors = get_theme_colors(current_theme)
    
    # Build CSS by combining all style components
    css = f"""
    <style>
    {get_layout_styles(colors["bg_color"], colors["text_color"], colors["control_bg"])}
    
    {get_sidebar_styles(colors["bg_color"], colors["text_color"], colors["control_bg"])}
    
    {get_sidebar_toggle_styles(colors["bg_color"], colors["text_color"], colors["control_bg"])}
    
    {get_form_styles(colors["bg_color"], colors["text_color"], colors["input_bg"])}
    
    {get_button_styles()}
    
    /* Dataframe styling to respect theme */
    .stDataFrame {{
        background-color: {colors["bg_color"]} !important;
        color: {colors["text_color"]} !important;
    }}
    
    .stDataFrame > div {{
        background-color: {colors["bg_color"]} !important;
    }}
    
    /* Table headers and cells */
    .stDataFrame table {{
        background-color: {colors["bg_color"]} !important;
        color: {colors["text_color"]} !important;
    }}
    
    /* Dataframe header row - white in light theme */
    .stDataFrame th {{
        background-color: {colors["bg_color"]} !important;
        color: {colors["text_color"]} !important;
        border-color: {'#e2e8f0' if current_theme == 'light' else colors["control_bg"]} !important;
    }}
    
    /* Target the header row more specifically */
    .stDataFrame thead th {{
        background-color: {colors["bg_color"]} !important;
        color: {colors["text_color"]} !important;
    }}
    
    /* Dataframe header cells in light theme */
    [data-testid="stDataFrame"] th,
    [data-testid="stDataFrame"] thead th {{
        background-color: {colors["bg_color"]} !important;
        color: {colors["text_color"]} !important;
    }}
    
    .stDataFrame td {{
        background-color: {colors["bg_color"]} !important;
        color: {colors["text_color"]} !important;
        border-color: {colors["control_bg"]} !important;
    }}
    
    /* Page headers with neutral colors */
    h1, h2, h3, h4, h5, h6 {{
        color: {'#4a5568' if current_theme == 'light' else '#a0aec0'} !important;
    }}
    
    /* Main page title */
    .main h1 {{
        color: {'#2d3748' if current_theme == 'light' else '#cbd5e0'} !important;
    }}
    
    /* File uploader styling for theme compatibility */
    section[data-testid="stFileUploadDropzone"] {{
        background-color: {colors["control_bg"]} !important;
    }}
    
    section[data-testid="stFileUploadDropzone"] small {{
        color: {'#4a5568' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    /* Drag and drop area - comprehensive targeting for all themes */
    [data-testid="stFileUploadDropzone"] > div,
    [data-testid="stFileUploadDropzone"] > div > div,
    [data-testid="stFileUploadDropzone"] div,
    [data-testid="stFileUploaderDropzone"],
    [data-testid="stFileUploaderDropzoneInstructions"],
    [data-testid="stFileUploaderDropzoneInstructions"] div {{
        background-color: {colors["control_bg"]} !important;
        color: {'#1a202c' if current_theme == 'light' else colors["text_color"]} !important;
        border-color: {'#cbd5e0' if current_theme == 'light' else '#4a5568'} !important;
    }}
    
    /* File uploader dropzone button */
    [data-testid="stFileUploadDropzone"] button,
    [data-testid="baseButton-secondary"] {{
        background-color: {colors["bg_color"]} !important;
        color: {'#1a202c' if current_theme == 'light' else colors["text_color"]} !important;
        border-color: {'#cbd5e0' if current_theme == 'light' else '#4a5568'} !important;
    }}
    
    /* Upload icon in drag-drop area */
    [data-testid="stFileUploadDropzone"] svg,
    [data-testid="stFileUploaderDropzoneInstructions"] svg {{
        color: {'#4a5568' if current_theme == 'light' else colors["text_color"]} !important;
        fill: {'#4a5568' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    /* Fix drag-drop text elements */
    [data-testid="stFileUploadDropzone"] p,
    [data-testid="stFileUploadDropzone"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] p {{
        color: {'#1a202c' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    /* File uploader limit text */
    [data-testid="stFileUploadDropzone"] small,
    [data-testid="stFileUploaderDropzoneInstructions"] small {{
        color: {'#4a5568' if current_theme == 'light' else '#a0aec0'} !important;
    }}
    
    /* File uploader label */
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] > label > div {{
        color: {'#1a202c' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    /* Uploaded file name */
    [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"],
    [data-testid="stFileUploader"] .uploadedFileName {{
        color: {'#1a202c' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    /* Radio button labels */
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] label span,
    [data-testid="stRadio"] label p,
    .stRadio label {{
        color: {'#1a202c' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    /* Text input fields - fix text color in light theme */
    [data-testid="stTextInput"] input,
    [data-testid="stTextInput"] label,
    .stTextInput input,
    .stTextInput label {{
        color: {'#1a202c' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    [data-testid="stTextInput"] input {{
        background-color: {'#ffffff' if current_theme == 'light' else colors["control_bg"]} !important;
    }}
    
    /* General labels and markdown in light theme */
    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown label {{
        color: {'#1a202c' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    /* Tabs styling - fix text visibility in light theme */
    [data-baseweb="tab-list"] button,
    [data-baseweb="tab"] {{
        color: {'#1a202c' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    [data-baseweb="tab-list"] button[aria-selected="true"],
    [data-baseweb="tab-highlight"] {{
        color: {'#3182ce' if current_theme == 'light' else '#63b3ed'} !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] button {{
        color: {'#4a5568' if current_theme == 'light' else colors["text_color"]} !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        color: {'#3182ce' if current_theme == 'light' else '#63b3ed'} !important;
    }}
    
    /* Buttons - add border for better visibility in light theme */
    .stButton > button {{
        border: 1px solid {'#cbd5e0' if current_theme == 'light' else '#4a5568'} !important;
    }}
    
    /* Primary buttons keep their accent styling */
    .stButton > button[kind="primary"] {{
        border: none !important;
    }}
    
    /* Page header/toolbar fix for light theme */
    header[data-testid="stHeader"] {{
        background-color: {colors["bg_color"]} !important;
    }}
    
    /* Target the specific header class mentioned */
    .st-emotion-cache-h4xjwg,
    [class*="st-emotion-cache"] header,
    header > div {{
        background-color: {colors["bg_color"]} !important;
        color: {colors["text_color"]} !important;
    }}
    
    /* Streamlit toolbar at top */
    .stApp > header {{
        background-color: {colors["bg_color"]} !important;
    }}
    
    /* Fix for all header elements */
    [data-testid="stHeader"],
    [data-testid="stToolbar"] {{
        background-color: {colors["bg_color"]} !important;
        color: {colors["text_color"]} !important;
    }}
    
    /* Error/Warning/Info notifications - fix text visibility in light theme */
    [data-testid="stNotification"],
    [data-testid="stAlert"],
    .stAlert,
    .stException,
    div[data-baseweb="notification"] {{
        color: #1a202c !important;
    }}
    
    [data-testid="stNotification"] p,
    [data-testid="stNotification"] span,
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span,
    .stAlert p,
    .stAlert span,
    div[data-baseweb="notification"] p,
    div[data-baseweb="notification"] span {{
        color: #1a202c !important;
    }}
    
    /* Error notification specific */
    [data-testid="stNotification"][data-type="error"],
    .stException {{
        color: #742a2a !important;
    }}
    
    [data-testid="stNotification"][data-type="error"] p,
    [data-testid="stNotification"][data-type="error"] span,
    .stException p,
    .stException span {{
        color: #742a2a !important;
    }}
    </style>
    """
    
    # Apply the CSS to the application
    st.markdown(css, unsafe_allow_html=True) 