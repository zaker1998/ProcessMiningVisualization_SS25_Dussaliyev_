from typing import Dict, Tuple, Optional, List, Set, cast
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
from logger import get_logger
from mining_algorithms.inductive_mining import InductiveMining

logger = get_logger("InductiveMiningDF")


class InductiveMiningDF(InductiveMining):
    """
    Inductive Mining Directly-Follows (IMd) variant.
    
    This is a simplified variant that filters weak directly-follows edges 
    from the DFG to produce cleaner, more understandable process models.
    
    The algorithm filters edges whose frequency is below:
        threshold = max_edge_frequency * edge_threshold
    
    
    Attributes:
    -----------
    edge_threshold : float
        Threshold for filtering weak edges (0.0 - 1.0).
        - 0.0 = no filtering (equivalent to standard miner)
        - 0.1 = filter edges below 10% of max frequency (recommended)
        - 0.5 = aggressive filtering (only keep strong edges)
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        """
        Initialize the IMd miner.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Event log as a dictionary mapping traces to frequencies
        """
        super().__init__(log)
        self.edge_threshold: float = 0.1
        logger.info("Initialized IMd (Directly-Follows) miner")

    def generate_graph(
        self,
        activity_threshold: float = 0.0,
        traces_threshold: float = 0.2,
        edge_threshold: float = 0.1
    ):
        """
        Generate process tree using IMd algorithm.
        
        Parameters:
        -----------
        activity_threshold : float
            Minimum frequency threshold for activities (0.0 - 1.0)
        traces_threshold : float  
            Minimum frequency threshold for traces (0.0 - 1.0)
        edge_threshold : float
            Minimum frequency threshold for edge filtering (0.0 - 1.0)
            
        Raises:
        -------
        ValueError
            If edge_threshold is not in valid range [0.0, 1.0]
        """
        # Validate edge_threshold
        if not (0.0 <= edge_threshold <= 1.0):
            logger.warning(f"Invalid edge_threshold {edge_threshold}, clamping to [0.0, 1.0]")
            edge_threshold = max(0.0, min(1.0, edge_threshold))
            
        self.edge_threshold = edge_threshold
        logger.info(f"Starting IMd mining with edge_threshold={edge_threshold}")
        
        # Call parent to perform standard filtering and mining
        super().generate_graph(activity_threshold, traces_threshold)

    def calculate_cut(self, log: Dict[Tuple[str, ...], int]) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Calculate cuts using filtered DFG approach.
        
        Strategy:
        1. If edge_threshold > 0: Try filtered DFG first (recommended)
        2. If no cut found: Fallback to full DFG
        
        This two-phase approach balances noise filtering with completeness.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log for cut detection
            
        Returns:
        --------
        Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]
            (operator, [sublogs...]) if a cut is found, otherwise None
        """
        if not log:
            logger.debug("Empty log provided to calculate_cut")
            return None
            
        # Phase 1: Try filtered DFG if filtering is enabled
        if self.edge_threshold > 0.0:
            try:
                logger.debug(f"Phase 1: Trying filtered DFG (threshold={self.edge_threshold})")
                filtered_dfg = self._create_filtered_dfg(log)
                
                # Try cuts on filtered DFG
                cut = self._try_all_cuts(filtered_dfg, log)
                if cut:
                    logger.info(f"Found {cut[0]} cut on filtered DFG")
                    return cut
                else:
                    logger.debug("No cuts found on filtered DFG, trying full DFG")
                    
            except Exception as e:
                logger.warning(f"Error with filtered DFG: {e}, falling back to full DFG")
        
        # Phase 2: Fallback to full DFG
        try:
            logger.debug("Phase 2: Trying full DFG")
            full_dfg = DFG(log)
            cut = self._try_all_cuts(full_dfg, log)
            if cut:
                logger.info(f"Found {cut[0]} cut on full DFG")
                return cut
                
        except Exception as e:
            logger.error(f"Error with full DFG: {e}")
        
        logger.debug("No cuts found")
        return None

    def _try_all_cuts(
        self, 
        dfg: DFG, 
        log: Dict[Tuple[str, ...], int]
    ) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Try all cut types on the given DFG.
        
        Cut order: exclusive → sequence → parallel → loop
        This order is standard in Inductive Mining algorithms.
        
        Parameters:
        -----------
        dfg : DFG
            Directly-follows graph to analyze
        log : Dict[Tuple[str, ...], int]
            Log for splitting
            
        Returns:
        --------
        Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]
            First valid cut found, or None
        """
        if not dfg or not log:
            return None
            
        # Define cuts to try (operator_name, cut_function, split_function)
        cuts = [
            ("xor", exclusive_cut, exclusive_split),
            ("seq", sequence_cut, sequence_split),
            ("par", parallel_cut, parallel_split),
            ("loop", loop_cut, loop_split)
        ]
        
        for op_name, cut_func, split_func in cuts:
            try:
                # Try to find partition
                if partitions := cut_func(dfg):
                    # Split log based on partition
                    # Cast to expected type for split function
                    splits = split_func(log, cast(List[Set[str]], partitions))
                    
                    # Validate split quality
                    if self._basic_split_validation(splits, log):
                        logger.debug(f"Valid {op_name} cut found")
                        return (op_name, splits)
                    else:
                        logger.debug(f"{op_name} cut rejected by validation")
                        
            except Exception as e:
                logger.debug(f"Error trying {op_name} cut: {e}")
                continue
                
        return None

    def _create_filtered_dfg(self, log: Dict[Tuple[str, ...], int]) -> DFG:
        """
        Create a filtered DFG by removing weak edges.
        
        Algorithm:
        1. Compute all edge frequencies from the log
        2. Calculate threshold = max_frequency * edge_threshold
        3. Keep only edges with frequency >= threshold
        4. Preserve all nodes and start/end information
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log
            
        Returns:
        --------
        DFG
            Filtered directly-follows graph
        """
        if not log:
            logger.debug("Empty log provided to _create_filtered_dfg")
            return DFG()
        
        # Step 1: Compute edge frequencies
        edge_freq = self._compute_edge_frequencies(log)
        
        if not edge_freq:
            logger.debug("No edges found in log")
            return DFG()
        
        # Step 2: Calculate threshold
        max_freq = max(edge_freq.values())
        threshold = max_freq * self.edge_threshold
        
        # Ensure minimum threshold is at least 1 (to filter single occurrences)
        if self.edge_threshold > 0 and threshold < 1:
            threshold = 1
            
        logger.debug(f"Edge filtering: max_freq={max_freq}, threshold={threshold}")
        
        # Step 3: Build filtered DFG
        dfg = DFG()
        
        # Add all nodes (preserve all activities)
        activities = self.get_log_alphabet(log)
        for activity in activities:
            dfg.add_node(activity)
        
        # Add edges above threshold
        retained_edges = 0
        for (src, tgt), freq in edge_freq.items():
            if freq >= threshold:
                dfg.add_edge(src, tgt)
                retained_edges += 1
        
        # Log statistics
        total_edges = len(edge_freq)
        retention_rate = retained_edges / total_edges if total_edges > 0 else 0
        logger.info(f"Edge filtering: {retained_edges}/{total_edges} edges retained ({retention_rate:.1%})")
        
        # Provide feedback on filtering aggressiveness
        if retention_rate < 0.2:
            logger.warning(f"Aggressive filtering: only {retention_rate:.1%} edges retained. "
                         f"Consider lowering edge_threshold if model is too simple.")
        elif retention_rate > 0.9 and self.edge_threshold > 0.05:
            logger.info(f"Light filtering: {retention_rate:.1%} edges retained. "
                       f"Consider increasing edge_threshold for more simplification.")
        
        # Step 4: Preserve start/end nodes
        self._preserve_start_end_nodes(dfg, log)
        
        return dfg

    def _compute_edge_frequencies(self, log: Dict[Tuple[str, ...], int]) -> Dict[Tuple[str, str], int]:
        """
        Compute frequency of each directly-follows edge in the log.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log with traces and frequencies
            
        Returns:
        --------
        Dict[Tuple[str, str], int]
            Dictionary mapping edges (source, target) to their frequencies
        """
        edge_freq: Dict[Tuple[str, str], int] = {}
        
        for trace, freq in log.items():
            # Skip traces with less than 2 activities
            if len(trace) < 2:
                continue
                
            # Count all directly-follows relations
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                edge_freq[edge] = edge_freq.get(edge, 0) + freq
                
        return edge_freq

    def _preserve_start_end_nodes(self, dfg: DFG, log: Dict[Tuple[str, ...], int]):
        """
        Preserve start and end node information in the DFG.
        
        Start nodes are first activities in traces.
        End nodes are last activities in traces.
        
        Parameters:
        -----------
        dfg : DFG
            The DFG to update
        log : Dict[Tuple[str, ...], int]
            Original log for extracting start/end information
        """
        try:
            if hasattr(dfg, 'start_nodes') and hasattr(dfg, 'end_nodes'):
                # Extract start and end activities from all traces
                start_nodes: Set[str | int] = {trace[0] for trace in log.keys() if trace}
                end_nodes: Set[str | int] = {trace[-1] for trace in log.keys() if trace}
                
                dfg.start_nodes = start_nodes
                dfg.end_nodes = end_nodes
                
                logger.debug(f"Preserved start nodes: {start_nodes}")
                logger.debug(f"Preserved end nodes: {end_nodes}")
                
        except Exception as e:
            logger.debug(f"Could not preserve start/end nodes: {e}")

    def get_edge_threshold(self) -> float:
        """
        Get the current edge threshold value.
        
        Returns:
        --------
        float
            Current edge threshold for filtering (0.0 - 1.0)
        """
        return self.edge_threshold
        
    def set_edge_threshold(self, threshold: float):
        """
        Set the edge threshold value.
        
        Parameters:
        -----------
        threshold : float
            New edge threshold value (0.0 - 1.0)
            
        Raises:
        -------
        ValueError
            If threshold is not in valid range
        """
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"Edge threshold must be between 0.0 and 1.0, got {threshold}")
        self.edge_threshold = threshold
        logger.debug(f"Edge threshold updated to {threshold}")

