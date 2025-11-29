# Define constants and configurations that don't depend on UI modules

# colon_substitute is used to replace the colon in event names to make them compatible with graphviz.
colon_substitute = "___"

# cluster seperator is used in the Fuzzy Mining algorithm to sepearte the events in the clusters.
cluster_seperator = "---"

# IMPORT FILE CONFIGURATIONS
# --------------------------

# The allowed file extensions for importing data.
import_file_types_mapping = {
    "csv": [".csv"],
    "pickle": [".pickle", ".pkl"],
    "xes": [".xes"],  # XES (eXtensible Event Stream) files for process mining
}
# List of all allowed file extensions.
import_file_suffixes = [
    suffix for suffixes in import_file_types_mapping.values() for suffix in suffixes
]

# GRAPH EXPORT CONFIGURATIONS
# ---------------------------

graph_export_mime_types = {
    "svg": "image/svg",
    "png": "image/png",
    "dot": "text/plain",
}

graph_export_formats = list(map(lambda x: x.upper(), graph_export_mime_types.keys()))

# COLUMN TYPE PREDICTION CONFIGURATIONS
column_types_predictions_values = {
    "time": set(["time", "date"]),
    "event": set(["event", "activity", "action", "task", "operation"]),
    "case": set(["case", "process", "instance", "session"]),
}

# ALGORITHM CONFIGURATIONS
# ------------------------

# Maps the algorithm names to the route names.
algorithm_mappings = {
    "Heuristic Mining": "heuristic",
    "Fuzzy Mining": "fuzzy",
    "Inductive Mining": "inductive",
}
# Maps the algorithm routes to the paths of the documentation files.
# Use relative paths from the src directory (where app.py runs from)
import os
_docs_base = os.path.join(os.path.dirname(__file__), "..", "docs", "algorithms")
docs_path_mappings = {
    "heuristic": os.path.normpath(os.path.join(_docs_base, "heuristic_miner.md")),
    "fuzzy": os.path.normpath(os.path.join(_docs_base, "fuzzy_miner.md")),
    "inductive": os.path.normpath(os.path.join(_docs_base, "inductive_miner.md")),
}

# Import UI modules only if they can be found (i.e., not when running tests)
try:
    from ui.pages.algorithms.heuristic.heuristic_miner_controller import HeuristicMinerController
    from ui.pages.algorithms.fuzzy.fuzzy_miner_controller import FuzzyMinerController
    from ui.pages.algorithms.inductive.inductive_miner_controller import InductiveMinerController

    # Maps the algorithm routes to the controllers.
    algorithm_routes = {
        "heuristic": HeuristicMinerController,
        "fuzzy": FuzzyMinerController,
        "inductive": InductiveMinerController,
    }
except ImportError:
    # Define dummy controllers for testing
    algorithm_routes = {
        "heuristic": None,
        "fuzzy": None,
        "inductive": None,
    }
