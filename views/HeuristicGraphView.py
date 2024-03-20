from views.AlgorithmViewInterface import AlgorithmViewInterface
from mining_algorithms.heuristic_mining import HeuristicMining
from graphs.visualization.heuristic_graph import HeuristicGraph
import streamlit as st


# To get max frequency run miner once with default parameter and then run them again with the sliders values
# start mining is only called once at old implementation. not at all the reruns after the values changed
class HeuristicGraphView(AlgorithmViewInterface):

    def initialize_values(self):
        if "frequency" not in st.session_state:
            st.session_state.frequency = 1
        if "threshhold" not in st.session_state:
            st.session_state.threshhold = 0.5

    def perform_mining(self, cases: list[list[str, ...]]) -> HeuristicGraph:
        miner = HeuristicMining(cases)
        return miner.create_dependency_graph_with_graphviz(
            self.get_slider_value("threshhold"),
            self.get_slider_value("frequency"),
        )

    def render_sliders(self):
        self.add_slider(0, 25, 1, "Minimum Frequency", "frequency")
        self.add_slider(0.0, 1.0, 0.1, "Threshhold", "threshhold")

    def get_page_title(self) -> str:
        return "Heuristic Mining"
