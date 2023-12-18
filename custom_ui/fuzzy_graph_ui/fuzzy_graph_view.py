from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from api.custom_error import FileNotFoundException
from custom_ui.heuristic_graph_ui.fuzzy_graph_controller import FuzzyGraphController
from custom_ui.algorithm_view_interface import AlgorithmViewInterface
from custom_ui.d3_html_widget import HTMLWidget
from custom_ui.custom_widgets import SaveProjectButton, ExportButton, CustomQSlider

class FuzzyGraphView(QWidget, AlgorithmViewInterface):
    def __int__(self, parent, saveFolder = "saves/", workingDirectory = 'temp/graph_viz'):
        super().__int__()