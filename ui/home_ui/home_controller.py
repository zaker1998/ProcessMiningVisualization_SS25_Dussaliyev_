import streamlit as st
from ui.base_ui.base_controller import BaseController
from analysis.detection_model import DetectionModel
from io_operations.import_operations import ImportOperations


class HomeController(BaseController):

    def __init__(self, views=None):
        self.detection_model = DetectionModel()
        self.import_model = ImportOperations()
        if views is None:
            from ui.home_ui.home_view import HomeView

            views = [HomeView()]
        super().__init__(views)

    def get_page_title(self) -> str:
        return ""

    def process_session_state(self):
        super().process_session_state()
        self.uploaded_file = st.session_state.get("uploaded_file", None)

    def process_file(self, selected_view):
        if self.uploaded_file is None:
            return

        # TODO: catch exceptions if file is not supported, if exception is used in the detection_model
        file_type = self.detection_model.detect_file_type(self.uploaded_file)

        if file_type == "csv":
            line = self.import_model.read_line(self.uploaded_file)
            detected_delimiter = self.detection_model.detect_delimiter(line)
            self.uploaded_file.seek(0)
            selected_view.display_df_import(detected_delimiter)
        elif file_type == "pickle":
            model = self.import_model.read_model(self.uploaded_file)
            selected_view.display_model_import(model)
        else:
            # add logging here for unsupported file format, and display error message
            # will most likely be moved to a except block
            st.session_state.error = "File format not supported"
            st.rerun()

    def set_model_and_algorithm(self, model, algorithm):
        st.session_state.model = model
        st.session_state.algorithm = algorithm

    def set_df(self, delimiter):
        if delimiter == "":
            st.session_state.error = "Please enter a delimiter"
            # change routing to home
            st.session_state.page = "Home"
            return
        st.session_state.df = self.import_model.read_csv(self.uploaded_file, delimiter)

    def run(self, selected_view, index):
        self.selected_view = selected_view
        selected_view.display_intro()
        selected_view.display_file_upload()
        if self.uploaded_file is not None:
            self.process_file(selected_view)
