from views.HeuristicGraphView import HeuristicGraphView
from views.FuzzyGraphView import FuzzyGraphView

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
