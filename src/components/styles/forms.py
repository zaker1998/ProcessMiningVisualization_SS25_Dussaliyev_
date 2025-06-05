"""
Styling for form elements and input components.
This module contains CSS styles for form-related UI elements.
"""

def get_form_styles(bg_color, text_color, input_bg):
    """
    Generate styles for form elements.
    
    Parameters
    ----------
    bg_color : str
        Background color for the main application area
    text_color : str
        Text color for the application
    input_bg : str
        Background color for input elements
        
    Returns
    -------
    str
        CSS styles for form elements
    """
    return f"""
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
    """ 