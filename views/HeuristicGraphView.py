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
        if "threshold" not in st.session_state:
            st.session_state.threshold = 0.5

        if "max_frequency" not in st.session_state:
            st.session_state.max_frequency = HeuristicMining(
                st.session_state.cases
            ).get_max_frequency()

    def perform_mining(self, cases: list[list[str, ...]]) -> HeuristicGraph:
        miner = HeuristicMining(cases)

        return miner.create_dependency_graph_with_graphviz(
            st.session_state.threshold,
            st.session_state.frequency,
        )

    def render_sliders(self):
        # if key="frequency" is used, the session state is lost after 1 rerun
        st.session_state.frequency = st.slider(
            "Minimum Frequency",
            1,
            st.session_state.max_frequency,
            value=st.session_state.frequency,
        )

        st.session_state.threshold = st.slider(
            "Threshold", 0.0, 1.0, value=st.session_state.threshold
        )

    def get_page_title(self) -> str:
        return "Heuristic Mining"

    def clear(self):
        del st.session_state.frequency
        del st.session_state.threshold
        del st.session_state.max_frequency
        super().clear()
