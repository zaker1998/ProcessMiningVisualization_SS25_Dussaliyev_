from ui.base_ui.base_controller import BaseController
from ui.export_ui.export_view import ExportView
import streamlit as st
from components.buttons import to_home, navigate_to
from io_operations.export_operations import ExportOperations
from io_operations.import_operations import ImportOperations
from analysis.detection_model import DetectionModel


class ExportController(BaseController):
    """Controller for the Export page."""

    # TODO: extract in own file for reuse and for better maintainability
    formats = ["SVG", "PNG", "DOT"]

    def __init__(self, views=None):
        """Initializes the controller for the Export page.

        Parameters
        ----------
        views : List[BaseView] | BaseView, optional
            The views for the Export page. If None is passed, the default view is used, by default None
        """
        if views is None:
            from ui.export_ui.export_view import ExportView

            views = [ExportView()]

        self.export_model = ExportOperations()
        self.import_model = ImportOperations()
        self.detection_model = DetectionModel()
        super().__init__(views)

    def get_page_title(self) -> str:
        """Returns the page title.

        Returns
        -------
        str
            The page title.
        """
        return "Export"

    def process_session_state(self):
        """Processes the session state. Checks if a model has been selected and if a graph has been generated.
        If not, an error message is displayed and the user is navigated back to the home page or alforithm page.
        User input for the DPI and export format is processed.
        """
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

    def export_graph(self, format: str) -> str:
        """Exports the graph in the specified format to a temporary file ont the disk and returns the file path.

        Parameters
        ----------
        format : str
            The format to export the graph to.

        Returns
        -------
        str
            The file path of the exported graph.
        """
        self.export_model.export_graph(self.graph, "temp/graph", format, dpi=self.dpi)
        return "temp/graph" + "." + format.lower()

    def read_png(self, file_path: str) -> str:
        """Reads the PNG file from the disk and returns the image.

        Parameters
        ----------
        file_path : str
            The file path of the PNG file.

        Returns
        -------
        str
            The image of the PNG file encoded as base64 string.
        """
        image = self.import_model.read_img(file_path)
        return image

    def pickle_model(self) -> bytes:
        """Pickle the model and return it as bytes.

        Returns
        -------
        bytes
            The model pickled as bytes.
        """
        return self.export_model.export_model_to_bytes(self.mining_model)

    def read_file(self, file_path: str) -> tuple[bytes, str]:
        """Reads the file from the disk and returns the content and MIME type.

        Parameters
        ----------
        file_path : str
            The file path of the file to read.

        Returns
        -------
        tuple[bytes, str]
            The content of the file as bytes and the MIME type of the file.
        """
        mime = self.detection_model.detect_mime_type(file_path)
        file_content = self.import_model.read_file_binary(file_path)

        return file_content, mime

    def run(self, selected_view, index):
        """Runs the controller for the Export page. This method is called to display the Export page and to react to user input.

        Parameters
        ----------
        selected_view : BaseView
            The view to display the import view.
        index : int
            The index of the selected view.
        """
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
