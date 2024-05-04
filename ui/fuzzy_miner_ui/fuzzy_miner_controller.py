from ui.base_algorithm_ui.base_algorithm_controller import BaseAlgorithmController
import streamlit as st
from mining_algorithms.fuzzy_mining import FuzzyMining
from ui.fuzzy_miner_ui.fuzzy_miner_view import FuzzyMinerView


class FuzzyMinerController(BaseAlgorithmController):

    def __init__(self, views=None, mining_model_class=None):
        if views is None:
            views = [FuzzyMinerView()]

        if mining_model_class is None:
            mining_model_class = FuzzyMining

        super().__init__(views, mining_model_class)

    def get_page_title(self) -> str:
        return "Fuzzy Mining"

    def process_algorithm_parameters(self):
        # set session state from instance variables if not set
        if "significance" not in st.session_state:
            st.session_state.significance = self.mining_model.get_significance()

        if "correlation" not in st.session_state:
            st.session_state.correlation = self.mining_model.get_correlation()

        if "edge_cutoff" not in st.session_state:
            st.session_state.edge_cutoff = self.mining_model.get_edge_cutoff()

        if "utility_ratio" not in st.session_state:
            st.session_state.utility_ratio = self.mining_model.get_utility_ratio()

        # set instance variables from session state
        self.significance = st.session_state.significance
        self.correlation = st.session_state.correlation
        self.edge_cutoff = st.session_state.edge_cutoff
        self.utility_ratio = st.session_state.utility_ratio

    def perform_mining(self) -> None:
        self.mining_model.create_graph_with_graphviz(
            self.significance, self.correlation, self.edge_cutoff, self.utility_ratio
        )

    def have_parameters_changed(self) -> bool:
        return (
            self.mining_model.get_significance() != self.significance
            or self.mining_model.get_correlation() != self.correlation
            or self.mining_model.get_edge_cutoff() != self.edge_cutoff
            or self.mining_model.get_utility_ratio() != self.utility_ratio
        )

    def get_sidebar_values(self) -> dict[str, tuple[int | float, int | float]]:
        sidebar_values = {
            "significance": (0.0, 1.0),
            "correlation": (0.0, 1.0),
            "edge_cutoff": (0.0, 1.0),
            "utility_ratio": (0.0, 1.0),
        }

        return sidebar_values
