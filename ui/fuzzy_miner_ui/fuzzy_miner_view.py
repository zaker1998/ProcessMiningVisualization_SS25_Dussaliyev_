from ui.base_algorithm_ui.base_algorithm_view import BaseAlgorithmView
import streamlit as st


class FuzzyMinerView(BaseAlgorithmView):
    def __init__(self):
        super().__init__()

    def get_page_title(self) -> str:
        return "Fuzzy Mining"

    def render_sidebar(
        self, sidebar_values: dict[str, tuple[int | float, int | float]]
    ) -> None:
        st.write("Significance Cutoff")
        st.slider(
            label="Significance",
            min_value=sidebar_values["significance"][0],
            max_value=sidebar_values["significance"][1],
            key="significance",
            help="Significance measures the frequency of events that are observed more frequently and are therefore considered more significant.",
        )

        st.slider(
            label="Correlation",
            min_value=sidebar_values["correlation"][0],
            max_value=sidebar_values["correlation"][1],
            key="correlation",
            help="Correlation measures how closely related two events following one another are.",
        )

        st.write("Edge filtering")

        st.slider(
            label="Edge Cutoff",
            min_value=sidebar_values["edge_cutoff"][0],
            max_value=sidebar_values["edge_cutoff"][1],
            key="edge_cutoff",
            help="The edge cutoff parameter determines the aggressiviness of the algorithm, i.e. the higher its value, the more likely the algorithm remove edges.",
        )

        st.slider(
            label="Utility Ratio",
            min_value=sidebar_values["utility_ratio"][0],
            max_value=sidebar_values["utility_ratio"][1],
            key="utility_ratio",
            help="A configuratable utility ratio determines the weight and a larger value for utility ratio will perserve more significant edges, while a smaller value will favor highly correlated edges",
        )
