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
        Lightweight quantile-based bucketing for node sizing.
        Returns original frequencies and a list of scale labels (>=1.0).
        """
        try:
            if not frequency:
                return [], []
            values = list(frequency)
            # Remove negatives and sort
            values_sorted = sorted(v for v in values if v >= 0)
            if not values_sorted:
                return values, [1.0 for _ in values]
            # Compute simple quantiles (quartiles)
            n = len(values_sorted)
            def q(p: float) -> float:
                if n == 1:
                    return values_sorted[0]
                idx = min(max(int(p * (n - 1)), 0), n - 1)
                return values_sorted[idx]
            q1 = q(0.25)
            q2 = q(0.50)
            q3 = q(0.75)
            max_v = values_sorted[-1]
            # Map each frequency to a bucket-based scale
            labels: List[float] = []
            for v in values:
                if v <= q1:
                    labels.append(1.0)
                elif v <= q2:
                    labels.append(1.5)
                elif v <= q3:
                    labels.append(2.0)
                elif v < max_v:
                    labels.append(2.5)
                else:
                    labels.append(3.0)
            return values, labels
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