from views.AlgorithmViewInterface import AlgorithmViewInterface
from graphs.visualization.heuristic_graph import HeuristicGraph
from controllers.HeuristicMiningController import (
    HeuristicMiningController,
)

from mining_algorithms.heuristic_mining import HeuristicMining
import streamlit as st
from components.sliders import slider


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
        slider(
            label="Minimum Frequency",
            min_value=1,
            max_value=self.max_frequency,
            key="frequency",
            setValue=self.controller.set_frequency,
            tooltip="Minimum frequency for displaying edges. Edges with a lower frequency (weight) will be removed.",
        )

        slider(
            label="Dependency Threshold",
            min_value=0.0,
            max_value=1.0,
            key="threshold",
            setValue=self.controller.set_threshold,
            tooltip="Minimum dependency for displaying edges. Edges with a lower dependency will be removed.",
        )

    def get_page_title(self) -> str:
        return "Heuristic Mining"
