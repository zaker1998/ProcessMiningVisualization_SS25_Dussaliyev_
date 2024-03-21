from views.HeuristicGraphView import HeuristicGraphView
from views.FuzzyGraphView import FuzzyGraphView

supported_exel_types = [
    "xls",
    "xlsx",
    "xlsm",
    "xlsb",
    "odf",
    "ods",
    "odt",
]

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
