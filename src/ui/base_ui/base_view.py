import streamlit as st
from abc import ABC
from exceptions.type_exceptions import InvalidTypeException
from logger import get_logger


class BaseView(ABC):
    """Base class for the views. It provides the basic layout and methods for the views."""

    controller = None
    logger = get_logger("BaseView")

    def create_layout(self):
        """Creates the layout for the views."""
        self._apply_theme_css()
        return

    def _apply_theme_css(self):
        """Applies the CSS for the current theme."""
        # Get current theme from session state
        theme = "dark" if "theme" not in st.session_state else st.session_state.theme
        
        # Define theme variables
        theme_vars = {
            "dark": {
                "--bg-primary": "#121212",
                "--bg-secondary": "#1e1e1e",
                "--bg-card": "#2d3748",
                "--bg-highlight": "#4a5568",
                "--text-primary": "#ffffff",
                "--text-secondary": "#e2e8f0",
                "--accent-primary": "#4299e1",
                "--accent-secondary": "#63b3ed",
                "--accent-hover": "#3182ce",
                "--shadow": "rgba(0, 0, 0, 0.3)",
                "--success-color": "#57B868",
                "--info-color": "#629AFF",
                "--warning-color": "#FFB259",
                "--danger-color": "#FF705B",
                "--sidebar-text": "#e2e8f0",
                "--form-text": "#ffffff",
                "--form-border": "#4a5568",
                "--sidebar-bg": "#0e1117",
                "--main-bg": "#0e1117",
                "--control-bg": "#262730",
            },
            "light": {
                "--bg-primary": "#ffffff",
                "--bg-secondary": "#f7fafc",
                "--bg-card": "#edf2f7",
                "--bg-highlight": "#e2e8f0",
                "--text-primary": "#1a202c",
                "--text-secondary": "#4a5568",
                "--accent-primary": "#3182ce",
                "--accent-secondary": "#4299e1",
                "--accent-hover": "#2b6cb0",
                "--shadow": "rgba(0, 0, 0, 0.1)",
                "--success-color": "#48bb78",
                "--info-color": "#4299e1",
                "--warning-color": "#ed8936",
                "--danger-color": "#f56565",
                "--sidebar-text": "#1a202c",
                "--form-text": "#1a202c",
                "--form-border": "#e2e8f0",
                "--sidebar-bg": "#f0f2f6",
                "--main-bg": "#ffffff",
                "--control-bg": "#f0f2f6",
            }
        }
        
        # CSS as an f-string to include theme variables
        css = f"""
        <style>
            :root {{
                {'; '.join([f"{k}: {v}" for k, v in theme_vars[theme].items()])}
            }}
            
            /* Base styling for the entire app */
            .block-container {{
                padding-top: 0rem;
                padding-bottom: 1rem;
                background-color: var(--bg-primary);
                transition: background-color 0.3s ease;
            }}
            
            /* Main app background */
            .main .block-container,
            [data-testid="stAppViewContainer"],
            .stApp {{
                background-color: var(--main-bg) !important;
            }}
            
            /* Dark mode Streamlit elements override */
            body {{ 
                background-color: var(--main-bg) !important; 
                color: var(--text-primary) !important; 
            }}
            
            /* Headers */
            .block-container h1, .block-container h2, .block-container h3 {{
                color: var(--text-primary) !important;
                transition: color 0.3s ease;
            }}
            
            /* Force sidebar text color to ensure visibility in both themes */
            .css-10oheav, .css-12w0qpk, .css-1dp5vir, .css-1l40rmt,
            [data-testid="stSidebarUserContent"] {{
                color: var(--text-primary) !important;
            }}
            
            /* Fix sidebar titles */
            [data-testid="stSidebar"] h1, 
            [data-testid="stSidebar"] h2, 
            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] .stMarkdown p,
            [data-testid="stSidebar"] .stMarkdown span {{
                color: var(--text-primary) !important;
            }}
            
            /* Fix sidebar captions */
            [data-testid="stSidebar"] .stCaption {{
                color: var(--text-secondary) !important;
            }}
            
            /* Fix sidebar elements */
            [data-testid="stSidebar"],
            [data-testid="stSidebarContent"] {{
                background-color: var(--sidebar-bg) !important;
            }}
            
            /* Fix wrap/unwrap buttons */
            [data-testid="baseButton-headerNoPadding"],
            button[kind="headerNoPadding"] {{
                background-color: var(--control-bg) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--form-border) !important;
                opacity: 1 !important;
                visibility: visible !important;
            }}
            
            /* Fix sidebar text inputs */
            [data-testid="stSidebar"] input, 
            [data-testid="stSidebar"] textarea {{
                color: var(--text-primary) !important;
            }}
            
            /* Mining variant dropdown fix */
            div[data-testid="stForm"] {{
                background-color: transparent !important;
                border-color: var(--form-border) !important;
            }}
            
            /* Fix dropdown menu items and popups */
            div[data-baseweb="popover"] ul,
            div[data-baseweb="popover"] li,
            div[data-baseweb="select-dropdown"],
            div[data-baseweb="select-dropdown"] ul,
            div[data-baseweb="select-dropdown"] li {{
                color: var(--text-primary) !important;
                background-color: var(--control-bg) !important;
            }}
            
            /* Cards with animations */
            .highlight-card {{
                background-color: var(--bg-card);
                border-radius: 8px;
                padding: 16px;
                padding-bottom: 6px !important;
                box-shadow: 0 4px 6px var(--shadow);
                margin-bottom: 20px;
                color: var(--text-primary);
                transition: background-color 0.3s ease, color 0.3s ease;
            }}
            
            
            /* Section headers */
            .section-header {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 15px;
                color: var(--text-primary);
                background-color: var(--accent-primary);
                padding: 8px 15px;
                border-radius: 5px;
                display: inline-block;
                transition: background-color 0.3s ease, color 0.3s ease;
            }}
            
            /* Feature items with animations */
            .feature-item {{
                background-color: var(--bg-highlight);
                color: var(--text-primary);
                padding: 10px 15px;
                border-radius: 5px;
                margin-bottom: 12px;
                font-size: 16px;
                display: flex;
                align-items: center;
                transition: color 0.3s ease;
            }}
            
            
            /* Feature icons */
            .feature-icon {{
                font-size: 20px;
                margin-right: 10px;
                color: var(--accent-secondary);
                transition: color 0.3s ease;
            }}
            
            /* Buttons with animations */
            .stButton>button {{
                background-color: var(--accent-primary);
                color: white;
                border-radius: 5px;
                border: none;
                padding: 10px 15px;
                font-size: 16px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            .stButton>button:hover {{
                background-color: var(--accent-hover);
                box-shadow: 0 4px 8px var(--shadow);
            }}
            
            .stButton>button:active {{
                transform: scale(0.95);
            }}
            
            /* Sample data section styling */
            .sample-data-section {{
                margin-top: 1.5rem;
                margin-bottom: 1.5rem;
            }}
            
            .sample-data-button {{
                text-align: center;
                border-radius: 8px !important;
                font-weight: 500 !important;
                height: 2.8rem !important;
                margin-top: 0.5rem !important;
                box-shadow: 0 2px 4px var(--shadow) !important;
            }}
            
            /* Sample data button hover effect */
            .sample-data-button:hover {{
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 8px var(--shadow) !important;
            }}
            
            /* Sample data header */
            .sample-data-header {{
                margin-bottom: 0.5rem !important;
                font-weight: 600 !important;
                color: var(--accent-primary) !important;
            }}
            
            /* File uploader improvements */
            .stFileUploader {{
                background-color: var(--bg-secondary);
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                border: 2px dashed var(--accent-secondary);
                transition: border-color 0.3s ease;
            }}
            
            .stFileUploader:hover {{
                border-color: var(--accent-primary);
            }}
            
            /* Ripple effect for buttons */
            .stButton>button::after {{
                content: '';
                position: absolute;
                width: 100%;
                height: 100%;
                top: 0;
                left: 0;
                pointer-events: none;
                background-image: radial-gradient(circle, rgba(255, 255, 255, 0.3) 10%, transparent 10.01%);
                background-repeat: no-repeat;
                background-position: 50%;
                transform: scale(10, 10);
                opacity: 0;
                transition: transform 0.5s, opacity 1s;
            }}
            
            .stButton>button:active::after {{
                transform: scale(0, 0);
                opacity: 0.3;
                transition: 0s;
            }}
            
            /* Selectbox styling */
            .stSelectbox label {{
                color: var(--text-primary);
                transition: color 0.3s ease;
            }}
            
            /* Other Streamlit elements */
            .stTextInput>div>div {{
                background-color: var(--bg-secondary);
                color: var(--text-primary);
                transition: background-color 0.3s ease, color 0.3s ease;
            }}
            
            /* Fix for alignment of columns */
            .row-widget.stHorizontal {{
                align-items: center !important;
            }}
            
            /* Add spacing between elements */
            .stText, .stMarkdown {{
                margin-bottom: 0.5rem;
            }}
            
            /* Tooltip styling */
            .stTooltipIcon {{
                color: var(--text-secondary) !important;
            }}
            
            /* Radio button styling */
            .stRadio > div {{
                background-color: transparent !important;
                padding: 10px;
                border-radius: 5px;
            }}
            
            /* Expander styling */
            .streamlit-expanderHeader {{
                background-color: var(--bg-highlight) !important;
                color: var(--text-primary) !important;
            }}
            
            .streamlit-expanderContent {{
                background-color: var(--bg-secondary) !important;
                color: var(--text-primary) !important;
            }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)

    def display_error_message(self, error_message: str):
        """Displays an error message on the page.

        Parameters
        ----------
        error_message : str
            The error message to be displayed.
        """
        st.error(error_message)

    def display_success_message(self, success_message: str):
        """Displays a success message on the page.

        Parameters
        ----------
        success_message : str
            The success message to be displayed.
        """
        st.success(success_message)

    def display_info_message(self, info_message: str):
        """Displays an info message on the page.

        Parameters
        ----------
        info_message : str
            The info message to be displayed.
        """
        st.info(info_message)

    def display_warning_message(self, warning_message: str):
        """Displays a warning message on the page.

        Parameters
        ----------
        warning_message : str
            The warning message to be displayed.
        """
        st.warning(warning_message)

    def display_page_title(self, title: str):
        """Displays the title of the page.

        Parameters
        ----------
        title : str
            The title of the page.
        """
        st.title(title)

    def set_controller(self, controller):
        """Sets the controller for the view.

        Parameters
        ----------
        controller : BaseController
            The controller for the view.

        Raises
        ------
        InvalidTypeException
            If the controller is not a subclass of BaseController.
        """
        from ui.base_ui.base_controller import BaseController

        if not any(cls.__name__ == 'BaseController' for cls in type(controller).__mro__):
            self.logger.error(
                f"Invalid controller type: {type(controller)}, expected: {BaseController}"
            )
            raise InvalidTypeException(BaseController, type(controller))
        self.controller = controller

    def display_progress_indicator(self, step, total_steps, step_names=None):
        """
        Displays a progress indicator showing the current step in a multi-step process.
        
        Parameters
        ----------
        step : int
            Current step (1-indexed)
        total_steps : int
            Total number of steps
        step_names : list[str], optional
            Names for each step
        """
        if step_names is None:
            step_names = [f"Step {i+1}" for i in range(total_steps)]
        
        progress = (step - 1) / (total_steps - 1) if total_steps > 1 else 1.0
        st.progress(progress)
        
        # Create clickable step indicators
        cols = st.columns(total_steps)
        for i in range(total_steps):
            with cols[i]:
                style = "color: #4299e1; font-weight: bold;" if i == step-1 else "color: gray;"
                st.markdown(f"<p style='text-align: center; {style}'>{step_names[i]}</p>", 
                            unsafe_allow_html=True)
