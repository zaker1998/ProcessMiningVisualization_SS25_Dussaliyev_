"""
Configuration module for the Process Mining Tool.
This module contains all the global configurations, constants, and mappings used throughout the application.
"""

from typing import Dict, Set, List
from ui.heuristic_miner_ui.heuristic_miner_controller import HeuristicMinerController
from ui.fuzzy_miner_ui.fuzzy_miner_controller import FuzzyMinerController
from ui.inductive_miner_ui.inductive_miner_controller import InductiveMinerController

# String manipulation constants
COLON_SUBSTITUTE: str = "___"  # Used to replace colons in event names for Graphviz compatibility
CLUSTER_SEPARATOR: str = "---"  # Used in Fuzzy Mining algorithm to separate events in clusters

# File import configurations
IMPORT_FILE_TYPES_MAPPING: Dict[str, List[str]] = {
    "csv": [".csv"],
    "pickle": [".pickle", ".pkl"],
}

# List of all allowed file extensions
IMPORT_FILE_SUFFIXES: List[str] = [
    suffix for suffixes in IMPORT_FILE_TYPES_MAPPING.values() for suffix in suffixes
]

# Graph export configurations
GRAPH_EXPORT_MIME_TYPES: Dict[str, str] = {
    "svg": "image/svg",
    "png": "image/png",
    "dot": "text/plain",
}

GRAPH_EXPORT_FORMATS: List[str] = list(map(lambda x: x.upper(), GRAPH_EXPORT_MIME_TYPES.keys()))

# Column type prediction configurations
COLUMN_TYPES_PREDICTIONS: Dict[str, Set[str]] = {
    "time": {"time", "date"},
    "event": {"event", "activity", "action", "task", "operation"},
    "case": {"case", "process", "instance", "session"},
}

# Algorithm configurations
ALGORITHM_MAPPINGS: Dict[str, str] = {
    "Heuristic Mining": "heuristic",
    "Fuzzy Mining": "fuzzy",
    "Inductive Mining": "inductive",
}

DOCS_PATH_MAPPINGS: Dict[str, str] = {
    "heuristic": "docs/algorithms/heuristic_miner.md",
    "fuzzy": "docs/algorithms/fuzzy_miner.md",
    "inductive": "docs/algorithms/inductive_miner.md",
}

ALGORITHM_ROUTES: Dict[str, type] = {
    "heuristic": HeuristicMinerController,
    "fuzzy": FuzzyMinerController,
    "inductive": InductiveMinerController,
}
