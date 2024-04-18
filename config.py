from views.HeuristicGraphView import HeuristicGraphView
from views.FuzzyGraphView import FuzzyGraphView
from views.InductiveGraphView import InductiveGraphView
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
    "heuristic": HeuristicGraphView(),
    "fuzzy": FuzzyGraphView(),
    "inductive": InductiveGraphView(),
}


@st.cache_data
def get_algorithm_view(algorithm: str):
    return algorithm_routes[algorithm]
