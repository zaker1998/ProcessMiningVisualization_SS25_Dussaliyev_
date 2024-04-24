from views.AlgorithmViewInterface import AlgorithmViewInterface
from graphs.visualization.inductive_graph import InductiveGraph
from controllers.InductiveMiningController import (
    InductiveMiningController,
)

from mining_algorithms.inductive_mining import InductiveMining
import streamlit as st
from components.sliders import slider


class InductiveGraphView(AlgorithmViewInterface):

    def __init__(self):
        self.controller = InductiveMiningController()

    def is_correct_model_type(self, model) -> bool:
        return isinstance(model, InductiveMining)

    def initialize_values(self):
        if "activity_threshold" not in st.session_state:
            st.session_state.activity_threshold = (
                self.controller.get_activity_threshold()
            )

        if "minimum_traces_frequency" not in st.session_state:
            st.session_state.minimum_traces_frequency = (
                self.controller.get_minimum_traces_frequency()
            )

        self.maximum_trace_frequency = self.controller.get_maximum_trace_frequency()

    def render_sidebar(self):

        slider(
            label="Minimum Traces Frequency",
            min_value=1,
            max_value=self.maximum_trace_frequency,
            key="minimum_traces_frequency",
            setValue=self.controller.set_minimum_traces_frequency,
            tooltip="The minimum traces frequency parameter determines the minimum frequency of a trace to be included in the graph.",
        )

        slider(
            label="Activity Threshold",
            min_value=0.0,
            max_value=1.0,
            key="activity_threshold",
            setValue=self.controller.set_activity_threshold,
            tooltip="""The activity threshold parameter determines the minimum frequency of an activity to be included in the graph. 
            All activities with a frequency that is lower than (1-treshold) * max_event_frequency will be removed.
            The higher the value, the more activities will be included in the graph.""",
        )

    def get_page_title(self) -> str:
        return "Inductive Mining"
