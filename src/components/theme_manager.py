import streamlit as st

def theme_toggle():
    """
    Creates a toggle button for switching between light and dark themes.
    Returns the current theme name.
    """
    # Initialize theme in session state if not present
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"  # Default theme
    
    # Current theme
    current_theme = st.session_state.theme
    
    # Create a more visually appealing toggle
    st.write("### Theme")
    
    # Use custom HTML/CSS for better-looking buttons
    light_selected = current_theme == "light"
    dark_selected = current_theme == "dark"
    
    # Always use "primary" style for both buttons to keep them blue
    # Use the same styling for consistency
    
    # Create two buttons side by side
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔆 Light", 
                    key="light_theme", 
                    use_container_width=True,
                    type="primary"):  # Always primary for blue color
            if not light_selected:
                st.session_state.theme = "light"
                st.rerun()
    
    with col2:
        if st.button("🌙 Dark", 
                    key="dark_theme", 
                    use_container_width=True,
                    type="primary"):  # Always primary for blue color
            if not dark_selected:
                st.session_state.theme = "dark"
                st.rerun()
    
    # Add custom CSS to fix button sizing and styling
    button_fix_css = f"""
    <style>
        /* Make both buttons same blue color */
        button[data-testid="baseButton-primary"] {{
            background-color: #4b5eff !important;
            color: white !important;
            border: none !important;
            height: 40px !important;  /* Ensure consistent height */
            min-width: 100px !important;  /* Ensure minimum width */
        }}
        
        /* Add indicator for selected theme */
        button[data-testid="baseButton-primary"][aria-selected="true"] {{
            box-shadow: 0 0 0 2px white !important;
        }}
        
        /* Selected button indicator - add subtle highlight */
        button[key="light_theme"] {{
            border-bottom: {light_selected and "2px solid white" or "none"} !important;
            opacity: {light_selected and "1.0" or "0.85"} !important;
        }}
        
        button[key="dark_theme"] {{
            border-bottom: {dark_selected and "2px solid white" or "none"} !important;
            opacity: {dark_selected and "1.0" or "0.85"} !important;
        }}
    </style>
    """
    st.markdown(button_fix_css, unsafe_allow_html=True)
    
    return st.session_state.theme 