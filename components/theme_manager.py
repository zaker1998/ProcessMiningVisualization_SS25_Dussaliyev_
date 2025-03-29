import streamlit as st

def theme_toggle():
    """
    Creates a toggle button for switching between light and dark themes.
    Returns the current theme name.
    """
    # Initialize theme in session state if not present
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"  # Default theme
    
    # Create the toggle in the sidebar
    theme_emoji = "🌙" if st.session_state.theme == "light" else "☀️"
    theme_label = f"{theme_emoji} {st.session_state.theme.capitalize()} Mode"
    
    if st.button(theme_label, key="theme_toggle"):
        # Switch theme
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        # Force a rerun to apply theme immediately
        st.rerun()
        
    return st.session_state.theme 