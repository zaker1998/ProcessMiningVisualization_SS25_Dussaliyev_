from views.HeuristicGraphView import HeuristicGraphView
from views.FuzzyGraphView import FuzzyGraphView
import streamlit as st

# name : route
algorithm_mappings = {
    "Heuristic Mining": "heuristic",
    "Fuzzy Mining": "fuzzy",
}

# route : view
algorithm_routes = {
    "heuristic": HeuristicGraphView(),
    "fuzzy": FuzzyGraphView(),
}

print("config.py loaded")


@st.cache_data
def get_algorithm_view(algorithm: str):
    return algorithm_routes[algorithm]
