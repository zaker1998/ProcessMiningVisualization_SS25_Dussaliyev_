from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QTextEdit
from api.custom_error import FileNotFoundException
from custom_ui.fuzzy_graph_ui.fuzzy_graph_controller import FuzzyGraphController
from custom_ui.algorithm_view_interface import AlgorithmViewInterface
from custom_ui.d3_html_widget import HTMLWidget
from custom_ui.custom_widgets import SaveProjectButton, ExportButton, CustomQSlider

class FuzzyGraphView(QWidget, AlgorithmViewInterface):
    def __init__(self, parent, saveFolder = "saves/", workingDirectory = 'temp/graph_viz'):
        super().__init__()
        self.parent = parent
        self.initialized = False

        self.default_significance = 1
        self.default_correlation = 0.5

        self.saveFolder = saveFolder
        self.workingDirectory = workingDirectory # directory where graphviz file is stored for display and export
        self.FuzzyGraphController = FuzzyGraphController(workingDirectory, self.default_significance, self.default_correlation)

        self.graph_widget = HTMLWidget(parent)

        slider_frame = QFrame()
        slider_frame.setFrameShape(QFrame.StyledPanel)
        slider_frame.setFrameShadow(QFrame.Sunken)
        slider_frame.setMinimumWidth(200)

        slider_frame_layout = QVBoxLayout()
        slider_frame_layout.addWidget(QLabel("Fuzzy Mining Modifiers", alignment=Qt.AlignCenter))

        slider_frame.setLayout(slider_frame_layout)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.graph_widget, stretch=3)
        qlable = QLabel("Hello from the view of Fuzzy Miner")
        main_layout.addWidget(qlable)
        main_layout.addWidget(slider_frame, stretch=1)

        self.setLayout(main_layout)
    def startMining(self, filename, cases):
        return
    def generate_dot(self):
        return
    def generate_svg(self):
        return
    def generate_png(self):
        return
    def loadModel(self):
        return
    def clear(self):
        self.graph_widget.clear()
        self.default_significance = 1
        self.default_correlation = 0.5
        self.zoom_factor = 1.0