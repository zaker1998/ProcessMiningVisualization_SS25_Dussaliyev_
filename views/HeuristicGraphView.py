from views.AlgorithmViewInterface_new import AlgorithmViewInterface
from graphs.visualization.heuristic_graph import HeuristicGraph
from mining_algorithms.heuristic_miner.HeuristicMiningController import (
    HeuristicMiningController,
)
import streamlit as st


class HeuristicGraphView(AlgorithmViewInterface):

    def __init__(self):
        self.controller = HeuristicMiningController()

    def initialize_values(self):
        # find other way to initialize values, as the view should not directly access the controller
        if "threshold" not in st.session_state:
            st.session_state.threshold = self.controller.get_model().get_threshold()
        if "frequency" not in st.session_state:
            st.session_state.frequency = self.controller.get_model().get_frequency()
        self.max_frequency = self.controller.get_max_frequency()

    def render_sidebar(self):
        frequency = st.slider(
            "Minimum Frequency",
            1,
            self.max_frequency,
            key="frequency",
        )

        threshold = st.slider("Threshold", 0.0, 1.0, key="threshold")

        self.controller.set_frequency(frequency)
        self.controller.set_threshold(threshold)

    def get_page_title(self) -> str:
        return "Heuristic Mining"

    def clear(self):
        super().clear()
