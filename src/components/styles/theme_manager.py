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
    </style>
    """
    
    # Apply the CSS to the application
    st.markdown(css, unsafe_allow_html=True) 