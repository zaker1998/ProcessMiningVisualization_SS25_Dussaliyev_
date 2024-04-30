import streamlit as st
from abc import ABC, abstractmethod


class BaseController(ABC):

    def __init__(self, views=None):

        if views is None:
            # TODO: change to a more specific exception, add logging
            raise ValueError("At least one view must be provided to the controller")

        from base_ui.base_view import BaseView

        if isinstance(views, list) or isinstance(views, tuple):
            for view in views:
                if not issubclass(view, BaseView):
                    # TODO: change to a more specific exception, add logging
                    raise ValueError("All views must be subclasses of BaseView")
            self.views = list(views)
        else:
            if not issubclass(views, BaseView):
                # TODO: change to a more specific exception, add logging
                raise ValueError("All views must be subclasses of BaseView")
            self.views = [views]

        self.error_message = None
        self.info_message = None
        self.success_message = None
        self.warning_message = None

    def select_view(self):
        return self.views[0], 0

    def process_session_state(self):
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

    @abstractmethod
    def get_page_title(self) -> str:
        raise NotImplementedError(
            "Method get_page_title must be implemented in the child class"
        )

    def start(self):
        self.process_session_state()
        slected_view, pos = self.select_view()
        slected_view.set_controller(self)
        slected_view.create_layout()
        self.display_messages()
        select_view.display_page_title(self.get_page_title())
        self.run(slected_view, pos)

    @abstractmethod
    def run(self, slected_view, index):
        raise NotImplementedError("Method run must be implemented in the child class")
