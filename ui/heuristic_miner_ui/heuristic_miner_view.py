from ui.base_algorithm_ui.base_algorithm_view import BaseAlgorithmView
import streamlit as st


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
        st.slider(
            label="Minimum Frequency",
            min_value=sidebar_values["frequency"][0],
            max_value=sidebar_values["frequency"][1],
            key="frequency",
            help="Minimum frequency for displaying edges and nodes. Edges with a lower frequency (weight) will be removed. Node with a lower frequency will be removed.",
        )

        st.number_input(
            label=" ",
            min_value=sidebar_values["frequency"][0],
            max_value=sidebar_values["frequency"][1],
            value=st.session_state.frequency,
            key="frequency_text_input",
            on_change=self.set_session_state,
            args=("frequency", "frequency_text_input"),
        )

        st.slider(
            label="Dependency Threshold",
            min_value=sidebar_values["threshold"][0],
            max_value=sidebar_values["threshold"][1],
            key="threshold",
            help="Minimum dependency for displaying edges. Edges with a lower dependency will be removed.",
        )

        st.number_input(
            label=" ",
            min_value=sidebar_values["threshold"][0],
            max_value=sidebar_values["threshold"][1],
            value=st.session_state.threshold,
            key="threshold_text_input",
            on_change=self.set_session_state,
            args=("threshold", "threshold_text_input"),
        )

    def set_session_state(self, key, number_input_key) -> None:
        st.session_state[key] = st.session_state[number_input_key]
