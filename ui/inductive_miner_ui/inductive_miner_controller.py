from ui.base_algorithm_ui.base_algorithm_controller import BaseAlgorithmController
from ui.inductive_miner_ui.inductive_miner_view import InductiveMinerView
from mining_algorithms.inductive_mining import InductiveMining
import streamlit as st


class InductiveMinerController(BaseAlgorithmController):

    def __init__(self, views=None, mining_model_class=None):
        if views is None:
            views = [InductiveMinerView()]

        if mining_model_class is None:
            mining_model_class = InductiveMining
        super().__init__(views, mining_model_class)

    def get_page_title(self) -> str:
        return "Inductive Mining"

    def process_algorithm_parameters(self):
        # set session state from instance variables if not set
        if "traces_threshold" not in st.session_state:
            st.session_state.traces_threshold = self.mining_model.get_traces_threshold()

        if "activity_threshold" not in st.session_state:
            st.session_state.activity_threshold = (
                self.mining_model.get_activity_threshold()
            )

        # set instance variables from session state
        self.traces_threshold = st.session_state.traces_threshold
        self.activity_threshold = st.session_state.activity_threshold

    def perform_mining(self) -> None:
        self.mining_model.generate_graph(self.activity_threshold, self.traces_threshold)

    def have_parameters_changed(self) -> bool:
        return (
            self.mining_model.get_activity_threshold() != self.activity_threshold
            or self.mining_model.get_traces_threshold() != self.traces_threshold
        )

    def get_sidebar_values(self) -> dict[str, tuple[int | float, int | float]]:
        sidebar_values = {
            "traces_threshold": (0.0, 1.0),
            "activity_threshold": (0.0, 1.0),
        }

        return sidebar_values
