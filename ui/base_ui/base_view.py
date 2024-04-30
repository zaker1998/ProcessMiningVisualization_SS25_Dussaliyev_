import streamlit as st
from abc import ABC


class BaseView(ABC):
    controller = None

    def display_error_message(self, error_message):
        st.error(error_message)

    def display_success_message(self, success_message):
        st.success(success_message)

    def display_info_message(self, info_message):
        st.info(info_message)

    def display_warning_message(self, warning_message):
        st.warning(warning_message)

    def display_page_title(self, title):
        st.title(title)

    def set_controller(self, controller):
        from ui.base_ui.base_controller import BaseController

        if not isinstance(controller, BaseController):
            # TODO: add a logger and custom exception
            raise ValueError("All controllers must be subclasses of BaseController")
        self.controller = controller
