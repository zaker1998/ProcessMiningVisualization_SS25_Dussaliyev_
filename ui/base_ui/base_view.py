import streamlit as st
from abc import ABC


class BaseView(ABC):
    controller = None

    def create_layout(self):
        self.banner_container = st.container(use_container_width=True)
        self.title_container = st.container(use_container_width=True)

    def display_error_message(self, error_message):
        with self.banner_container:
            st.error(error_message)

    def display_success_message(self, success_message):
        with self.banner_container:
            st.success(success_message)

    def display_info_message(self, info_message):
        with self.banner_container:
            st.info(info_message)

    def display_warning_message(self, warning_message):
        with self.banner_container:
            st.warning(warning_message)

    def display_page_title(self, title):
        with self.title_container:
            st.title(title)

    def set_controller(self, controller):
        from ui.base_ui.base_controller import BaseController

        if not issubclass(controller, BaseController):
            # TODO: add a logger and custom exception
            raise ValueError("All controllers must be subclasses of BaseController")
        self.controller = controller
