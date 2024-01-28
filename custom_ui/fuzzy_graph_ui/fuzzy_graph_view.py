from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QFileDialog, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QTextEdit, QToolBox, QSpacerItem, QSizePolicy
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

        self.default_significance = 0.48
        self.significance = self.default_significance

        self.default_edge_cutoff = 0.4
        self.edge_cutoff = self.default_edge_cutoff

        self.default_utility_ration = 0.5
        self.utility_ratio = self.default_utility_ration

        self.max_significance = 100
        self.min_significance = 0

        self.max_edge_cutoff = 100
        self.min_edge_cutoff = 0

        self.max_utility_ratio = 100
        self.min_utility_ratio = 0

        self.saveFolder = saveFolder
        self.workingDirectory = workingDirectory # directory where graphviz file is stored for display and export
        self.FuzzyGraphController = FuzzyGraphController(workingDirectory, self.significance, self.edge_cutoff,self.utility_ratio)

        self.graphviz_graph = None
        self.graph_widget = HTMLWidget(parent)

        tool_box = QToolBox()
        option1_significance_widget = QWidget()
        option2_edge_filtering_widget = QWidget()

        slider_frame = QFrame()
        slider_frame.setFrameShape(QFrame.StyledPanel)
        slider_frame.setFrameShadow(QFrame.Sunken)
        slider_frame.setMinimumWidth(200)

        self.sign_slider = CustomQSlider(self.__sign_slider_changed, Qt.Vertical)
        self.sign_slider.setRange(self.min_significance, self.max_significance)
        #self.sign_slider.setValue(self.min_significance)

        self.edge_cutoff_slider = CustomQSlider(self.__edge_cutoff_slider_changed, Qt.Vertical)
        self.edge_cutoff_slider.setRange(self.min_edge_cutoff, self.max_edge_cutoff)
        #self.edge_cutoff_slider.setValue(self.min_edge_cutoff)

        self.utility_slider = CustomQSlider(self.__utility_slider_changed, Qt.Vertical)
        self.utility_slider.setRange(self.min_utility_ratio, self.max_utility_ratio)
        #self.utility_slider.setValue(self.min_utility_ratio)

        slider_layout = QHBoxLayout(option1_significance_widget)
        slider_layout.addWidget(self.sign_slider)

        slider_layout1 = QHBoxLayout(option2_edge_filtering_widget)
        slider_layout1.addWidget(self.edge_cutoff_slider)
        slider_layout1.addWidget(self.utility_slider)

        tool_box.addItem(option1_significance_widget, "Significance cutoff")
        tool_box.addItem(option2_edge_filtering_widget, "Edge filtering")

        self.saveProject_button = SaveProjectButton(self.parent, self.saveFolder, self.getModel)
        self.export_button = ExportButton(self.parent)

        # fist separating line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        # second separating line
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)

        slider_frame_layout = QVBoxLayout()
        slider_frame_layout.addWidget(QLabel("Fuzzy Mining Modifiers", styleSheet="color: blue;", alignment=Qt.AlignCenter))
        slider_frame_layout.addWidget(line)
        slider_frame_layout.addSpacing(20)
        slider_frame_layout.addWidget(tool_box, stretch=1)
        slider_frame_layout.addSpacing(20)
        slider_frame_layout.addWidget(line1)
        slider_frame_layout.addWidget(self.saveProject_button)
        slider_frame_layout.addWidget(self.export_button)

        slider_frame.setLayout(slider_frame_layout)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.graph_widget, stretch=4)
        main_layout.addWidget(slider_frame, stretch=1)

        self.setLayout(main_layout)

    def startMining(self, filename, cases):

        self.saveProject_button.load_filename(filename)
        self.FuzzyGraphController.startMining(cases)

        self.graph_widget.start_server()
        self.initialized = True
        self.__set_slider_values(self.default_significance, self.edge_cutoff, self.utility_ratio)
        # I have added a Qtimer, because while I was debuging the code it was trying to write the new value and redrawing
        # the new graph at the same time
        QTimer.singleShot(500, self.__redraw)
        #self.__redraw()

    def __sign_slider_changed(self, value):
        self.sign_slider.setText(f"Significance Value: {value/100:.2f}")
        self.significance = value/100

        # it will try to update model, but model not existin yet
        if not self.initialized:
            return

        print("Changing signification value")
        # mine and draw after changing signification value
        self.__redraw()

    def __edge_cutoff_slider_changed(self, value):
        self.edge_cutoff_slider.setText(f"Cutoff: {value/100:.2f}")
        self.edge_cutoff = value/100

        if not self.initialized:
            return
        print("Changing cutoff value")
        #self.__redraw()

    def __utility_slider_changed(self, value):
        self.utility_slider.setText(f"Utility: {value / 100:.2f}")
        self.utility_ratio = value / 100

        if not self.initialized:
            return
        print("Changing utility ration value")
        #self.__redraw()

    def __redraw(self):
        self.graphviz_graph = self.FuzzyGraphController.mine_and_draw(self.significance, self.edge_cutoff, self.utility_ratio)
        filename = self.workingDirectory + '.dot'
        self.graph_widget.set_source(filename)
        try:
            self.graph_widget.reload()
        except FileNotFoundException as e:
            print(e.message)
    def __set_slider_values(self, sign, cutoff, utility):
        # set text
        self.sign_slider.setText(f"Significance: {sign:.2f}")
        self.edge_cutoff_slider.setText(f"Cutoff: {cutoff:.2f}")
        self.utility_slider.setText(f"Utility: {utility:.2f}")

        # set value
        self.sign_slider.setValue(int(sign*100))
        self.edge_cutoff_slider.setValue(int(cutoff*100))
        self.utility_slider.setValue(int(utility * 100))
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
        # this values w
        #self.default_significance = 0.7
        #self.default_edge_cutoff = 0.5
        #self.default_utility_ration = 0.5
        self.zoom_factor = 1.0