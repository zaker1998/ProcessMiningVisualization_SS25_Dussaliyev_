"""
Styling for buttons and interactive elements.
This module contains CSS styles for button components.
"""

def get_button_styles():
    """
    Generate styles for buttons.
    
    Returns
    -------
    str
        CSS styles for buttons
    """
    return """
    /* Theme toggle buttons styling */
    .stButton > button {
        height: 40px !important;
        min-width: 100px !important;
    }
    
    /* Primary buttons styling */
    .stButton > button[data-testid="baseButton-primary"] {
        background-color: #4b5eff !important;
        color: white !important;
    }
    """ 