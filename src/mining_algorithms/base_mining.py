from __future__ import annotations
import numpy as np
from typing import Dict, List, Tuple, Set
from mining_algorithms.mining_interface import MiningInterface
from logger import get_logger

logger = get_logger("BaseMining")


class BaseMining(MiningInterface):
    """
    BaseMining provides shared utilities used by concrete miners.

    Responsibilities:
      - Extract activities and their frequencies from a trace-frequency log (dict)
      - Build succession matrix (directly-follows matrix)
      - Provide helper filters (events / traces)
      - Provide node sizing helpers used by visualization
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        super().__init__()
        self.log: Dict[Tuple[str, ...], int] = log
        # extracted values
        self.events: List[str]
        self.appearance_frequency: Dict[str, int]
        self.event_positions: Dict[str, int]
        self.succession_matrix: np.ndarray

        # initialize
        self.events, self.appearance_frequency = self.__filter_out_all_events()
        self.event_positions = {event: i for i, event in enumerate(self.events)}
        self.succession_matrix = self.__create_succession_matrix()

        # clustering helpers (kept for API compatibility)
        self.event_freq_sorted, self.event_freq_labels_sorted = self.get_clusters(
            list(self.appearance_frequency.values())
        )

        # start/end nodes
        self.start_nodes = self.__get_start_nodes()
        self.end_nodes = self.__get_end_nodes()

    # --- core extractors -------------------------------------------------
    def __filter_out_all_events(self) -> Tuple[List[str], Dict[str, int]]:
        """
        Create list of unique events and their total appearance counts.
        Input log format: dict[tuple(activity names...), frequency]
        """
        counts: Dict[str, int] = {}
        for trace, freq in self.log.items():
            for act in trace:
                counts[act] = counts.get(act, 0) + freq
        activities = list(counts.keys())
        return activities, counts

    def __get_start_nodes(self) -> Set[str]:
        """Return set of first activities in traces (non-empty traces only)."""
        return set(trace[0] for trace in self.log.keys() if len(trace) > 0)

    def __get_end_nodes(self) -> Set[str]:
        """Return set of last activities in traces (non-empty traces only)."""
        return set(trace[-1] for trace in self.log.keys() if len(trace) > 0)

    # --- succession matrix -----------------------------------------------
    def __create_succession_matrix(self) -> np.ndarray:
        """
        Build directly-follows matrix of shape (n_events, n_events) where
        matrix[i,j] counts transitions event_i -> event_j aggregated over the log.
        """
        n = len(self.events)
        matrix = np.zeros((n, n), dtype=int)
        for trace, freq in self.log.items():
            if len(trace) < 2:
                continue
            indices = [self.event_positions[a] for a in trace]
            src = indices[:-1]
            tgt = indices[1:]
            # accumulate frequencies to matrix at once
            np.add.at(matrix, (src, tgt), freq)
        return matrix

    # --- filtering helpers -----------------------------------------------
    def get_events_to_remove(self, threshold: float) -> Set[str]:
        """
        Return events whose frequency < threshold * max_frequency.
        threshold in [0,1]. Values outside are clamped.
        """
        if threshold > 1.0:
            threshold = 1.0
        elif threshold < 0.0:
            threshold = 0.0
        if not self.appearance_frequency:
            return set()
        minimum_event_freq = round(max(self.appearance_frequency.values()) * threshold)
        return {e for e, f in self.appearance_frequency.items() if f < minimum_event_freq}

    def calulate_minimum_traces_frequency(self, threshold: float) -> int:
        """
        Compute threshold frequency for traces (round(max_trace_frequency * threshold)).
        """
        if threshold > 1.0:
            threshold = 1.0
        elif threshold < 0.0:
            threshold = 0.0
        if not self.log:
            return 0
        return round(max(self.log.values()) * threshold)

    # --- visualization helpers -------------------------------------------
    def calulate_node_size(self, node: str) -> Tuple[float, float]:
        """
        Return (width, height) for a visual node based on cluster scaling.
        Uses event_freq_labels_sorted produced by clustering to map frequency -> scale.
        """
        scale_factor = self.get_scale_factor(node)
        width = (scale_factor / 2) + self.min_node_size
        height = width / 3
        return width, height

    def get_scale_factor(self, node: str) -> float:
        """
        Map a node frequency to a scale factor via the clustered labels.
        If mapping fails, return 1.0 as default.
        """
        node_freq = self.appearance_frequency.get(node, 0)
        try:
            idx = self.event_freq_sorted.index(node_freq)
            return self.event_freq_labels_sorted[idx]
        except Exception:
            return 1.0