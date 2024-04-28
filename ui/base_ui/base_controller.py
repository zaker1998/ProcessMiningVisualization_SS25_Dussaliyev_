import streamlit as st


# TODO: chnage structure to allow multiple views, that can be chosen by a value from  a session state.
# Create own function to choose a view, and store it in a variable in the controller.
class BaseController:

    def __init__(self, view=None, model=None):
        if view is not None:
            self.view = view

        if model is not None:
            self.model = model

        self.error_message = None
        self.info_message = None
        self.success_message = None
        self.warning_message = None

    def read_values_from_session_state(self):
        if "error" in st.session_state:
            self.error_message = st.session_state.error
            del st.session_state.error

        if "info" in st.session_state:
            self.info_message = st.session_state.info
            del st.session_state.info

        if "success" in st.session_state:
            self.success_message = st.session_state.success
            del st.session_state.success

        if "warning" in st.session_state:
            self.warning_message = st.session_state.warning
            del st.session_state.warning

    def display_messages(self):
        if self.error_message is not None:
            self.view.display_error_message(self.error_message)

        if self.info_message is not None:
            self.view.display_info_message(self.info_message)

        if self.success_message is not None:
            self.view.display_success_message(self.success_message)

        if self.warning_message is not None:
            self.view.display_warning_message(self.warning_message)

    def run(self):
        self.read_values_from_session_state()
        self.view.set_controller(self)
        self.view.create_layout()
        self.display_messages()
