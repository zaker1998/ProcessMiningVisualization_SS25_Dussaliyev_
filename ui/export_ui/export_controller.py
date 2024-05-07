from ui.base_ui.base_controller import BaseController
from ui.export_ui.export_view import ExportView
import streamlit as st
from components.buttons import to_home, navigate_to
from utils.io import read_img
from io_operations.export_operations import ExportOperations
from io_operations.import_operations import ImportOperations
from analysis.detection_model import DetectionModel


class ExportController(BaseController):
    formats = ["SVG", "PNG", "DOT"]

    def __init__(self, views=None):
        if views is None:
            from ui.export_ui.export_view import ExportView

            views = [ExportView()]

        self.export_model = ExportOperations()
        self.import_model = ImportOperations()
        self.detection_model = DetectionModel()
        super().__init__(views)

    def get_page_title(self) -> str:
        return "Export"

    def process_session_state(self):
        super().process_session_state()
        if "model" not in st.session_state:
            st.session_state.error = "Model not selected"
            to_home("Home")
            st.rerun()

        self.mining_model = st.session_state.model

        if self.mining_model.graph is None:
            st.session_state.error = "Graph not generated"
            navigate_to("Algorithm")

        if "dpi" not in st.session_state:
            st.session_state.dpi = 96

        if "export_format" not in st.session_state:
            st.session_state.export_format = "SVG"

        self.graph = self.mining_model.get_graph()
        self.dpi = st.session_state.dpi
        self.export_format = st.session_state.export_format

    def export_graph(self, format):
        self.export_model.export_graph(self.graph, "temp/graph", format, dpi=self.dpi)
        return "temp/graph" + "." + format.lower()

    def read_png(self, file_path):
        image = self.import_model.read_img(file_path)
        return image

    def pickle_model(self):
        return self.export_model.export_model_to_bytes(self.mining_model)

    def read_file(self, file_path):
        mime = self.detection_model.detect_mime_type(file_path)
        file_content = self.import_model.read_file_binary(file_path)

        return file_content, mime

    def run(self, selected_view, index):
        selected_view.display_back_button()
        selected_view.display_export_format(self.formats)
        if self.export_format == "PNG":
            selected_view.display_dpi_input(50, self.dpi, 1)

        selected_view.display_model_export_button("model.pickle", self.pickle_model())

        file_path = self.export_graph(format=self.export_format)
        file, mime = self.read_file(file_path)

        selected_view.display_export_button(
            "graph." + self.export_format.lower(), file, mime
        )
        if self.export_format != "PNG":
            png_file_path = self.export_graph(format="PNG")
        else:
            png_file_path = file_path
        png_file = self.read_png(png_file_path)

        selected_view.display_png(png_file)
