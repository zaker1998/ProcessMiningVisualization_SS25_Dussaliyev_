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
        significance = st.slider(
            "Significance",
            0.0,
            1.0,
            key="significance",
            help="Significance measures the frequency of events that are observed more frequently and are therefore considered more significant.",
        )

        correlation = st.slider(
            "Correlation",
            0.0,
            1.0,
            key="correlation",
            help="Correlation measures how closely related two events following one another are.",
        )

        st.divider()
        st.write("Edge filtering")
        edge_cutoff = st.slider(
            "Edge Cutoff",
            0.0,
            1.0,
            key="edge_cutoff",
            help="The edge cutoff parameter determines the aggressiviness of the algorithm, i.e. the higher its value, the more likely the algorithm remove edges",
        )

        utility_ratio = st.slider(
            "Utility Ration",
            0.0,
            1.0,
            key="utility_ration",
            help="A configuratable utility ratio determines the weight and a larger value for utility ratio will perserve more significant edges, while a smaller value will favor highly correlated edges",
        )

        self.controller.set_significance(significance)
        self.controller.set_correlation(correlation)
        self.controller.set_edge_cutoff(edge_cutoff)
        self.controller.set_utility_ratio(utility_ratio)

    def get_page_title(self) -> str:
        return "Fuzzy Mining"
