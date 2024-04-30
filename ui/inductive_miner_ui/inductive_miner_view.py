from ui.base_algorithm_ui.base_algorithm_view import BaseAlgorithmView
import steamlit as st


class InductiveMinerView(BaseAlgorithmView):

    def get_page_title(self) -> str:
        return "Inductive Mining"

    def render_sidebar(
        self, sidebar_values: dict[str, tuple[int | float, int | float]]
    ) -> None:
        st.slider(
            label="Traces Threshold",
            min_value=slider_values["traces_treshold"][0],
            max_value=slider_values["traces_treshold"][1],
            key="traces_treshold",
            help="""The traces threshold parameter determines the minimum frequency of a trace to be included in the graph. 
            All traces with a frequency that is lower than treshold * max_trace_frequency will be removed. The higher the value, the less traces will be included in the graph.""",
        )

        st.slider(
            label="Activity Threshold",
            min_value=slider_values["activity_threshold"][0],
            max_value=slider_values["activity_threshold"][1],
            key="activity_threshold",
            help="""The activity threshold parameter determines the minimum frequency of an activity to be included in the graph. 
            All activities with a frequency that is lower than treshold * max_event_frequency will be removed.
            The higher the value, the less activities will be included in the graph.""",
        )
