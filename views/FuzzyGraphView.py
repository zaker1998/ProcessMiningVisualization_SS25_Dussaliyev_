from views.AlgorithmViewInterface import AlgorithmViewInterface
from graphs.visualization.fuzzy_graph import FuzzyGraph
from mining_algorithms.fuzzy_mining import FuzzyMining
import streamlit as st


class FuzzyGraphView(AlgorithmViewInterface):

    def initialize_values(self):
        return

    def perform_mining(self, cases: list[list[str, ...]]) -> FuzzyGraph:
        miner = FuzzyMining(cases)
        graph = miner.create_graph_with_graphviz(
            st.session_state.significance,
            st.session_state.correlation,
            st.session_state.edge_cutoff,
            st.session_state.utility_ration,
        )
        return graph

    def render_sliders(self):
        st.write("Significance Cutoff")
        st.slider("Significance", 0.0, 1.0, key="significance")

        st.slider("Correlation", 0.0, 1.0, key="correlation")

        st.divider()
        st.write("Edge filtering")
        st.slider("Edge Cutoff", 0.0, 1.0, key="edge_cutoff")

        st.slider("Utility Ration", 0.0, 1.0, key="utility_ration")

    def get_page_title(self) -> str:
        return "Fuzzy Miner"

    def clear(self):
        del st.session_state.significance
        del st.session_state.correlation
        del st.session_state.edge_cutoff
        del st.session_state.utility_ration
        super().clear()
