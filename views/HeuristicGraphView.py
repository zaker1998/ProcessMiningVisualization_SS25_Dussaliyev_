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
            st.session_state.threshhold,
            st.session_state.frequency,
        )

    def render_sliders(self):
        # if key="frequency" is used, the session state is lost after 1 rerun
        freq = st.slider("Minimum Frequency", 0, 25, st.session_state.frequency)
        st.session_state.frequency = freq

        thresh = st.slider("Threshhold", 0.0, 1.0, st.session_state.threshhold)
        st.session_state.threshhold = thresh

    def get_page_title(self) -> str:
        return "Heuristic Mining"

    def clear(self):
        del st.session_state.frequency
        del st.session_state.threshhold
