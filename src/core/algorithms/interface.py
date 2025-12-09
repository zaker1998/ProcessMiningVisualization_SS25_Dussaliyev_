from abc import ABC
from typing import List, Optional, Tuple, Union
from utils.logger import get_logger
from core.graphs.visualization.base_graph import BaseGraph
from core.clustering.ddcal_clustering import DensityDistributionClusterAlgorithm

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
        Use the DDCAL (Density Distribution Cluster Algorithm) to cluster frequency data.
        
        The clusters are used to determine a scaling factor for nodes in the graph.
        DDCAL provides evenly distributed low-variance clusters, which is ideal for
        process mining visualization as it avoids over-emphasizing outliers.
        
        Reference:
            Lux, M., Rinderle-Ma, S. (2023):
            DDCAL: Evenly Distributing Data into Low Variance Clusters Based on Iterative Feature Scaling.
            Journal of Classification 40, 02. DOI: 10.1007/s00357-022-09428-6

        Parameters
        ----------
        frequency : List[float]
            The frequency data to be clustered

        Returns
        -------
        Tuple[List[float], List[float]]
            A tuple containing:
            - sorted_data: The frequency data sorted in ascending order
            - labels_sorted_data: The cluster labels (scale factors) for each sorted value
        """
        try:
            if not frequency:
                return [], []
            cluster = DensityDistributionClusterAlgorithm(frequency)
            return list(cluster.sorted_data), list(cluster.labels_sorted_data)
        except ZeroDivisionError as e:
            self.logger.error(f"Clustering ZeroDivisionError: {e}")
            self.logger.info("Clustering failed. Returning the original frequency.")
            return [frequency[0]] if frequency else [], [1.0] if frequency else []
        except Exception as e:
            self.logger.error(f"Clustering failed: {e}")
            return list(frequency), [1.0 for _ in frequency]

    def get_graph(self) -> Optional[BaseGraph]:
        """
        Return the produced graph. Subclasses should set self.graph in generate_graph.
        """
        return self.graph

    @classmethod
    def create_mining_instance(cls, *constructor_args):
        """Create a new instance using constructor args."""
        return cls(*constructor_args)