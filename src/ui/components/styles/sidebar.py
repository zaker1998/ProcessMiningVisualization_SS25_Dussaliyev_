"""
Styling for the sidebar component.
This module contains CSS styles for the sidebar and related elements.
"""

def get_sidebar_styles(bg_color, text_color, control_bg):
    """
    Generate sidebar styles for the application.
    
    Parameters
    ----------
    bg_color : str
        Background color for the main application area
    text_color : str
        Text color for the application
    control_bg : str
        Background color for control elements like the sidebar
        
    Returns
    -------
    str
        CSS styles for the sidebar
    """
    return f"""
    /* Sidebar styling - allows resizing */
    [data-testid="stSidebar"] {{
        background-color: {control_bg} !important;
    }}
    
    /* Adjust sidebar padding */
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }}
    
    /* Fix for all sidebar text */
    [data-testid="stSidebar"] * {{
        color: {text_color} !important;
    }}
    """

def get_sidebar_toggle_styles(bg_color, text_color, control_bg):
    """
    Generate styles for the sidebar toggle button.
    
    Parameters
    ----------
    bg_color : str
        Background color for the main application area
    text_color : str
        Text color for the application
    control_bg : str
        Background color for control elements like the sidebar
        
    Returns
    -------
    str
        CSS styles for the sidebar toggle button
    """
    return f"""
    /* Sidebar toggle button styling */
    button[kind="headerNoPadding"],
    [data-testid="baseButton-headerNoPadding"] {{
        background-color: {control_bg} !important;
        color: {text_color} !important;
        border: 1px solid rgba(49, 51, 63, 0.2) !important;
        visibility: visible !important;
        opacity: 1 !important;
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
        color: {text_color} !important;
    }}
    """ 