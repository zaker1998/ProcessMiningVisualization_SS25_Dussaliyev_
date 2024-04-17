from views.AlgorithmViewInterface import AlgorithmViewInterface
from graphs.visualization.inductive_graph import InductiveGraph
from controllers.InductiveMiningController import (
    InductiveMiningController,
)

from mining_algorithms.inductive_mining import InductiveMining
import streamlit as st


class InductiveGraphView(AlgorithmViewInterface):

    def __init__(self):
        self.controller = InductiveMiningController()

    def is_correct_model_type(self, model) -> bool:
        return isinstance(model, InductiveMining)

    def initialize_values(self):
        return

    def render_sidebar(self):
        return

    def get_page_title(self) -> str:
        return "Inductive Mining"
