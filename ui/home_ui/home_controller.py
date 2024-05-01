import streamlit as st
from ui.base_ui.base_controller import BaseController
from utils.io import read_file, detect_delimiter, pickle_load


class HomeController(BaseController):

    def __init__(self, views=None):
        if views is None:
            from ui.home_ui.home_view import HomeView

            views = [HomeView()]
        super().__init__(views)

    def get_page_title(self) -> str:
        return ""

    def process_file(self, file):
        # TODO: move io logic to a model
        if file.name.endswith(".csv"):
            detected_delimiter = ""
            try:
                detected_delimiter = detect_delimiter(file)
            except Exception as e:
                # TODO: use logging
                print(e)

            self.selected_view.display_df_import(detected_delimiter)
        elif file.name.endswith(".pickle"):
            model = pickle_load(file)
            self.selected_view.display_model_import(model)

    def set_model_and_algorithm(self, model, algorithm):
        st.session_state.model = model
        st.session_state.algorithm = algorithm

    def set_df(self, file, delimiter):
        if delimiter == "":
            st.session_state.error = "Please enter a delimiter"
            # change routing to home
            st.session_state.page = "Home"
            return
        # TODO: move io logic to a model
        st.session_state.df = read_file(file, delimiter=delimiter)

    def run(self, selected_view, index):
        self.selected_view = selected_view
        selected_view.display_intro()
        selected_view.display_file_upload()
