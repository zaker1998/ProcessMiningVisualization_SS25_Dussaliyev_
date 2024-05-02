from ui.base_algorithm_ui.base_algorithm_view import BaseAlgorithmView
import streamlit as st


class HeuristicMinerView(BaseAlgorithmView):

    def render_sidebar(
        self, sidebar_values: dict[str, tuple[int | float, int | float]]
    ) -> None:
        st.slider(
            label="Minimum Frequency",
            min_value=sidebar_values["frequency"][0],
            max_value=sidebar_values["frequency"][1],
            key="frequency",
            help="Minimum frequency for displaying edges and nodes. Edges with a lower frequency (weight) will be removed. Node with a lower frequency will be removed.",
        )

        st.slider(
            label="Dependency Threshold",
            min_value=sidebar_values["threshold"][0],
            max_value=sidebar_values["threshold"][1],
            key="threshold",
            help="Minimum dependency for displaying edges. Edges with a lower dependency will be removed.",
        )
