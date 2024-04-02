from views.AlgorithmViewInterface import AlgorithmViewInterface
from graphs.visualization.fuzzy_graph import FuzzyGraph
from controllers.FuzzyMiningController import (
    FuzzyMiningController,
)
from mining_algorithms.fuzzy_mining import FuzzyMining
import streamlit as st


class FuzzyGraphView(AlgorithmViewInterface):

    def __init__(self):
        self.controller = FuzzyMiningController()

    def is_correct_model_type(self, model) -> bool:
        return isinstance(model, FuzzyMining)

    def initialize_values(self):
        if "significance" not in st.session_state:
            st.session_state.significance = self.controller.get_significance()
        if "correlation" not in st.session_state:
            st.session_state.correlation = self.controller.get_correlation()
        if "edge_cutoff" not in st.session_state:
            st.session_state.edge_cutoff = self.controller.get_edge_cutoff()
        if "utility_ratio" not in st.session_state:
            st.session_state.utility_ratio = self.controller.get_utility_ratio()

    def render_sidebar(self):
        st.write("Significance Cutoff")
        significance = st.slider("Significance", 0.0, 1.0, key="significance")

        correlation = st.slider("Correlation", 0.0, 1.0, key="correlation")

        st.divider()
        st.write("Edge filtering")
        edge_cutoff = st.slider("Edge Cutoff", 0.0, 1.0, key="edge_cutoff")

        utility_ratio = st.slider("Utility Ration", 0.0, 1.0, key="utility_ration")

        self.controller.set_significance(significance)
        self.controller.set_correlation(correlation)
        self.controller.set_edge_cutoff(edge_cutoff)
        self.controller.set_utility_ratio(utility_ratio)

    def get_page_title(self) -> str:
        return "Fuzzy Mining"

    def clear(self):
        super().clear()
