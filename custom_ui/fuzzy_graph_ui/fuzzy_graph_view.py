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

        self.default_significance = 1.0
        self.significane = self.default_significance
        self.default_correlation = 0.3
        self.correlation = self.default_correlation

        self.max_significance = 100
        self.min_significance = 0
        self.max_correlation = 100
        self.min_correlation = 0

        self.saveFolder = saveFolder
        self.workingDirectory = workingDirectory # directory where graphviz file is stored for display and export
        self.FuzzyGraphController = FuzzyGraphController(workingDirectory, self.default_significance, self.default_correlation)

        self.graphviz_graph = None
        self.graph_widget = HTMLWidget(parent)

        slider_frame = QFrame()
        slider_frame.setFrameShape(QFrame.StyledPanel)
        slider_frame.setFrameShadow(QFrame.Sunken)
        slider_frame.setMinimumWidth(200)

        self.sign_slider = CustomQSlider(self.__sign_slider_changed, Qt.Vertical)
        self.sign_slider.setRange(self.min_significance, self.max_significance)
        self.sign_slider.setValue(self.min_significance)

        self.corr_slider = CustomQSlider(self.__corr_slider_changed, Qt.Vertical)
        self.corr_slider.setRange(self.min_correlation, self.max_correlation)
        self.corr_slider.setValue(self.min_correlation)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.sign_slider)
        slider_layout.addWidget(self.corr_slider)

        # TODO move it to mine_and_draw later
        self.__set_slider_values(self.max_significance, self.min_correlation)

        self.saveProject_button = SaveProjectButton(self.parent, self.saveFolder, self.getModel)
        self.export_button = ExportButton(self.parent)

        slider_frame_layout = QVBoxLayout()
        slider_frame_layout.addWidget(QLabel("Fuzzy Mining Modifiers", alignment=Qt.AlignCenter))
        slider_frame_layout.addLayout(slider_layout)
        slider_frame_layout.addWidget(self.saveProject_button)
        slider_frame_layout.addWidget(self.export_button)

        slider_frame.setLayout(slider_frame_layout)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.graph_widget, stretch=3)
        main_layout.addWidget(slider_frame, stretch=1)

        self.setLayout(main_layout)

    def startMining(self, filename, cases):

        self.saveProject_button.load_filename(filename)
        self.FuzzyGraphController.startMining(cases)
        # TODO DELETE it
        #self.graph_widget.start_server()

    def __sign_slider_changed(self, value):
        self.sign_slider.setText(f"Significance Value: {value/100:.2f}")
        self.significane = value/100

        # TODO mine and draw after changing signification value
    def __corr_slider_changed(self, value):
        self.corr_slider.setText(f"Correlation Value: {value/100:.2f}")
        self.correlation = value/100

        # TODO mine and draw after changing correlation value
    def __set_slider_values(self, sign, correlation):
        # set text
        self.sign_slider.setText(f"Significance Value: {sign:.2f}")
        self.corr_slider.setText(f"Correlation Value: {correlation:.2f}")

        # set value
        self.sign_slider.setValue(int(sign*100))
        self.corr_slider.setValue(int(correlation*100))
    def getModel(self):
        return self.FuzzyGraphController.getModel()
    def generate_dot(self):
        if not self.__ensure_graphviz_graph_exists():
            return
        self.graphviz_graph.render(self.workingDirectory, format = 'dot')
        prit("fuzzy_graph_view: DOT generated")
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