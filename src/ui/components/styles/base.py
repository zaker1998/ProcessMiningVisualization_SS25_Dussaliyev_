"""
Base styling for the application layout.
This module contains CSS styles for the main layout components.
"""

def get_layout_styles(bg_color, text_color, control_bg):
    """
    Generate layout styles for the application.
    
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
        CSS styles for the layout
    """
    return f"""
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
    """ 