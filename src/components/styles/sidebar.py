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
    """ 