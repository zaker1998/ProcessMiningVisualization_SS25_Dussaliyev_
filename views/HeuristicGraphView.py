from views.AlgorithmViewInterface import AlgorithmViewInterface
from graphs.visualization.heuristic_graph import HeuristicGraph
from controllers.HeuristicMiningController import (
    HeuristicMiningController,
)

from mining_algorithms.heuristic_mining import HeuristicMining
import streamlit as st


class HeuristicGraphView(AlgorithmViewInterface):

    def __init__(self):
        self.controller = HeuristicMiningController()

    def is_correct_model_type(self, model) -> bool:
        return isinstance(model, HeuristicMining)

    def initialize_values(self):
        if "threshold" not in st.session_state:
            st.session_state.threshold = self.controller.get_threshold()
        if "frequency" not in st.session_state:
            st.session_state.frequency = self.controller.get_frequency()
        self.max_frequency = self.controller.get_max_frequency()

    def render_sidebar(self):
        frequency = st.slider(
            "Minimum Frequency",
            1,
            self.max_frequency,
            key="frequency",
        )

        threshold = st.slider("Dependency Threshold", 0.0, 1.0, key="threshold")

        self.controller.set_frequency(frequency)
        self.controller.set_threshold(threshold)

    def get_page_title(self) -> str:
        return "Heuristic Mining"

    def clear(self):
        super().clear()
