from ui.heuristic_miner_ui.heuristic_miner_controller import HeuristicMinerController
from ui.fuzzy_miner_ui.fuzzy_miner_controller import FuzzyMinerController
from ui.inductive_miner_ui.inductive_miner_controller import InductiveMinerController
import streamlit as st

# name : route
algorithm_mappings = {
    "Heuristic Mining": "heuristic",
    "Fuzzy Mining": "fuzzy",
    "Inductive Mining": "inductive",
}
# route : path
docs_path_mappings = {
    "heuristic": "docs/algorithms/heuristic_miner.md",
    "fuzzy": "docs/algorithms/fuzzy_miner.md",
    "inductive": "docs/algorithms/inductive_miner.md",
}

# route : view
algorithm_routes = {
    "heuristic": HeuristicMinerController(),
    "fuzzy": FuzzyMinerController(),
    "inductive": InductiveMinerController(),
}


@st.cache_data
def get_algorithm_view(algorithm: str):
    return algorithm_routes[algorithm]
