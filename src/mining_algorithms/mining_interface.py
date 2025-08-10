from abc import ABC
from typing import List, Tuple, Union
from logger import get_logger
from graphs.visualization.base_graph import BaseGraph

logger = get_logger("MiningInterface")


class MiningInterface(ABC):
    """
    Base abstract interface for mining algorithm implementations.

    Subclasses should implement generate_graph(...) and expose get_graph().
    """

    def __init__(self):
        self.graph: BaseGraph | None = None
        self.min_node_size: float = 1.5
        self.logger = logger

    def get_clusters(
        self, frequency: List[float]
    ) -> Tuple[List[float], List[float]]:
        """
        Stub for clustering frequency values.
        The real implementation is expected to be provided by a clustering module.
        Keep this method here for backward compatibility with the old code.
        """
        # fallback simple behavior: scale all to 1.0 if any problem
        try:
            unique = sorted(set(frequency))
            labels = [1.0 for _ in frequency]
            return list(frequency), labels
        except Exception as e:
            self.logger.error("Clustering failed: %s", e)
            return frequency, [1.0 for _ in frequency]

    def get_graph(self) -> BaseGraph:
        """
        Return the produced graph. Subclasses should set self.graph in generate_graph.
        """
        return self.graph

    @classmethod
    def create_mining_instance(cls, *constructor_args):
        """Create a new instance using constructor args."""
        return cls(*constructor_args)