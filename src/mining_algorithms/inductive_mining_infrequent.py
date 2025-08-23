from typing import Dict, Tuple, Optional, List
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
from logger import get_logger
from mining_algorithms.inductive_mining import InductiveMining

logger = get_logger("InductiveMiningInfrequent")


class InductiveMiningInfrequent(InductiveMining):
    """
    Infrequent Inductive Miner:
    - First tries to find cuts on the full Directly-Follows Graph (DFG).
    - If no cut is found, falls back to a filtered DFG where low-frequency
      directly-follows relations are removed.
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        super().__init__(log)
        self.noise_threshold: float = 0.2
        self.max_recursion_depth: int = 100

    def generate_graph(
        self,
        activity_threshold: float = 0.0,
        traces_threshold: float = 0.2,
        noise_threshold: float = 0.2
    ):
        """
        Public entry point for process discovery.
        Allows tuning of noise_threshold to filter weak directly-follows edges.
        """
        self.noise_threshold = noise_threshold
        super().generate_graph(activity_threshold, traces_threshold)

    def calulate_cut(self, log: Dict[Tuple[str, ...], int]) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Attempt to discover a cut:
        1. Try cuts on the full DFG.
        2. If no cut found, try cuts on the filtered DFG.
        Returns:
            (operator, [sublogs...]) if a cut is found, otherwise None.
        """
        # Try with full DFG
        cut = self._try_cuts_on_dfg(DFG(log), log)
        if cut:
            return cut

        # Try with filtered DFG
        filtered_dfg = self._create_filtered_dfg(log)
        return self._try_cuts_on_dfg(filtered_dfg, log)

    def _try_cuts_on_dfg(self, dfg: DFG, log: Dict[Tuple[str, ...], int]) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Try to detect a cut using all available cut functions on the given DFG.
        Returns:
            (operator, [sublogs...]) if successful, otherwise None.
        """
        if partitions := exclusive_cut(dfg):
            return "xor", exclusive_split(log, partitions)
        if partitions := sequence_cut(dfg):
            return "seq", sequence_split(log, partitions)
        if partitions := parallel_cut(dfg):
            return "par", parallel_split(log, partitions)
        if partitions := loop_cut(dfg):
            return "loop", loop_split(log, partitions)
        return None

    def _create_filtered_dfg(self, log: Dict[Tuple[str, ...], int]) -> DFG:
        """
        Build a filtered DFG where only edges with frequency >=
        (noise_threshold * max_edge_freq) are retained.
        """
        dfg = DFG()
        activities = self.get_log_alphabet(log)

        # Add nodes
        for a in activities:
            dfg.add_node(a)

        # Compute edge frequencies
        edge_freq: Dict[Tuple[str, str], int] = {}
        for trace, freq in log.items():
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                edge_freq[edge] = edge_freq.get(edge, 0) + freq

        if not edge_freq:
            return dfg

        # Compute threshold
        max_freq = max(edge_freq.values())
        threshold = max_freq * self.noise_threshold

        # Add edges above threshold
        for (src, tgt), freq in edge_freq.items():
            if freq >= threshold:
                dfg.add_edge(src, tgt)

        # Preserve start/end nodes if supported
        if hasattr(dfg, "start_nodes"):
            try:
                dfg.start_nodes = {t[0] for t in log.keys()}
                dfg.end_nodes = {t[-1] for t in log.keys()}
            except Exception:
                pass

        return dfg
