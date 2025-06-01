from ui.base_algorithm_ui.base_algorithm_view import BaseAlgorithmView
import streamlit as st
from components.number_input_slider import number_input_slider


class HeuristicMinerView(BaseAlgorithmView):
    """View for the Heuristic Miner algorithm."""

    def render_sidebar(
        self, sidebar_values: dict[str, tuple[int | float, int | float]]
    ) -> None:
        """Renders the sidebar for the Heuristic Miner algorithm.

        Parameters
        ----------
        sidebar_values : dict[str, tuple[int  |  float, int  |  float]]
            A dictionary containing the minimum and maximum values for the sidebar sliders.
            The keys of the dictionary are equal to the keys of the sliders.
        """
        # Add header and description for parameter section
        st.markdown("### Heuristic Miner Parameters")
        st.caption("Adjust these parameters to control what is displayed in the process model")

        number_input_slider(
            label="Minimum Frequency",
            min_value=sidebar_values["frequency"][0],
            max_value=sidebar_values["frequency"][1],
            key="frequency",
            help="Minimum frequency for displaying edges and nodes. Edges with a lower frequency (weight) will be removed. Node with a lower frequency will be removed.",
        )

        number_input_slider(
            label="Dependency Threshold",
            min_value=sidebar_values["threshold"][0],
            max_value=sidebar_values["threshold"][1],
            key="threshold",
            help="Minimum dependency for displaying edges. Edges with a lower dependency will be removed.",
        )
        
        # Add helpful tip about parameters
        with st.expander("💡 Parameter Tips"):
            st.markdown("""
            - **Higher frequency values** will show only the most common paths
            - **Lower frequency values** will show more detailed, less common paths
            - **Higher dependency values** show only strong relationships
            - Adjust these parameters gradually to find the best visualization
            """)
