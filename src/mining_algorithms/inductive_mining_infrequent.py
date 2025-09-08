from typing import Dict, Tuple, Optional, List, Set
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
from logger import get_logger
from mining_algorithms.inductive_mining import InductiveMining
import hashlib

logger = get_logger("InductiveMiningInfrequent")


class InductiveMiningInfrequent(InductiveMining):
    """
    Infrequent Inductive Miner:
    - First tries to find cuts on the full Directly-Follows Graph (DFG).
    - If no cut is found, falls back to a filtered DFG where low-frequency
      directly-follows relations are removed.
    
    Improvements:
    - Better caching mechanism using content hashes
    - Improved edge filtering with adaptive thresholds
    - Enhanced error handling and validation
    - Better logging for debugging
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        super().__init__(log)
        self.noise_threshold: float = 0.2
        self.max_recursion_depth: int = 100
        # Use hash-based caching instead of storing full log as key
        self._edge_freq_cache: Dict[str, Dict[Tuple[str, str], int]] = {}
        self._log_stats_cache: Dict[str, Dict] = {}

    def generate_graph(
        self,
        activity_threshold: float = 0.0,
        traces_threshold: float = 0.2,
        noise_threshold: float = 0.2
    ):
        """
        Public entry point for process discovery.
        Allows tuning of noise_threshold to filter weak directly-follows edges.
        
        Parameters:
        -----------
        activity_threshold : float
            Minimum frequency threshold for activities (0.0 - 1.0)
        traces_threshold : float  
            Minimum frequency threshold for traces (0.0 - 1.0)
        noise_threshold : float
            Minimum frequency threshold for edge filtering (0.0 - 1.0)
        """
        if not (0.0 <= noise_threshold <= 1.0):
            logger.warning(f"Invalid noise_threshold {noise_threshold}, clamping to [0.0, 1.0]")
            noise_threshold = max(0.0, min(1.0, noise_threshold))
            
        self.noise_threshold = noise_threshold
        logger.info(f"Starting infrequent mining with noise_threshold={noise_threshold}")
        super().generate_graph(activity_threshold, traces_threshold)

    def calculate_cut(self, log: Dict[Tuple[str, ...], int]) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Attempt to discover a cut:
        1. Try cuts on the full DFG.
        2. If no cut found, try cuts on the filtered DFG.
        
        Returns:
            (operator, [sublogs...]) if a cut is found, otherwise None.
        """
        if not log:
            logger.debug("Empty log provided to calculate_cut")
            return None
            
        # Try with full DFG first
        try:
            full_dfg = DFG(log)
            cut = self._try_cuts_on_dfg(full_dfg, log)
            if cut:
                logger.debug(f"Found cut on full DFG: {cut[0]}")
                return cut
        except Exception as e:
            logger.warning(f"Error creating full DFG: {e}")

        # Try with filtered DFG
        try:
            filtered_dfg = self._create_filtered_dfg(log)
            cut = self._try_cuts_on_dfg(filtered_dfg, log)
            if cut:
                logger.debug(f"Found cut on filtered DFG: {cut[0]}")
            else:
                logger.debug("No cuts found on filtered DFG")
            return cut
        except Exception as e:
            logger.error(f"Error in filtered DFG processing: {e}")
            return None

    def _try_cuts_on_dfg(self, dfg: DFG, log: Dict[Tuple[str, ...], int]) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Try to detect a cut using all available cut functions on the given DFG.
        
        Returns:
            (operator, [sublogs...]) if successful, otherwise None.
        """
        if not dfg or not log:
            return None
            
        try:
            # Try cuts in standard order: exclusive, sequence, parallel, loop
            if partitions := exclusive_cut(dfg):
                splits = exclusive_split(log, partitions)
                if self._validate_split_quality(splits, log, "xor"):
                    return "xor", splits
                    
            if partitions := sequence_cut(dfg):
                splits = sequence_split(log, partitions)
                if self._validate_split_quality(splits, log, "seq"):
                    return "seq", splits
                    
            if partitions := parallel_cut(dfg):
                splits = parallel_split(log, partitions)
                if self._validate_split_quality(splits, log, "par"):
                    return "par", splits
                    
            if partitions := loop_cut(dfg):
                splits = loop_split(log, partitions)
                if self._validate_split_quality(splits, log, "loop"):
                    return "loop", splits
                    
        except Exception as e:
            logger.error(f"Error trying cuts on DFG: {e}")
            
        return None

    def _validate_split_quality(self, splits: List[Dict], log: Dict[Tuple[str, ...], int], cut_type: str) -> bool:
        """
        Validate the quality of a split to ensure it makes sense.
        
        Parameters:
        -----------
        splits : List[Dict]
            The splits produced by the cut
        log : Dict 
            Original log
        cut_type : str
            Type of cut ("xor", "seq", "par", "loop")
            
        Returns:
        --------
        bool
            True if split quality is acceptable
        """
        if not splits or len(splits) < 2:
            return False
            
        # Check that splits are non-empty and contain valid traces
        total_split_freq = 0
        for split in splits:
            if not split:
                logger.debug(f"Empty split found in {cut_type} cut")
                return False
            split_freq = sum(split.values())
            if split_freq == 0:
                logger.debug(f"Zero frequency split found in {cut_type} cut")
                return False
            total_split_freq += split_freq
            
        # Check frequency preservation (should roughly match original)
        original_freq = sum(log.values())
        if total_split_freq < original_freq * 0.8:  # Allow some tolerance
            logger.debug(f"Split frequency too low: {total_split_freq} vs {original_freq}")
            return False
            
        return True

    def _create_filtered_dfg(self, log: Dict[Tuple[str, ...], int]) -> DFG:
        """
        Build a filtered DFG where only edges with frequency >=
        (noise_threshold * max_edge_freq) are retained.
        
        Improvements:
        - Uses content-based caching for better performance
        - Adaptive threshold calculation for better results
        - Enhanced logging for debugging
        """
        if not log:
            logger.debug("Empty log provided to _create_filtered_dfg")
            return DFG()
        
        # Create hash-based cache key for better performance
        log_hash = self._create_log_hash(log)
        
        # Check cache first
        if log_hash in self._edge_freq_cache:
            edge_freq = self._edge_freq_cache[log_hash]
            logger.debug("Using cached edge frequencies")
        else:
            # Compute edge frequencies
            edge_freq = self._compute_edge_frequencies(log)
            self._edge_freq_cache[log_hash] = edge_freq
            
        # Build filtered DFG
        dfg = DFG()
        activities = self.get_log_alphabet(log)
        
        # Add all nodes first
        for activity in activities:
            dfg.add_node(activity)
        
        if not edge_freq:
            logger.debug("No edges found in log")
            return dfg
        
        # Calculate adaptive threshold
        threshold = self._calculate_adaptive_threshold(edge_freq)
        logger.debug(f"Using edge frequency threshold: {threshold}")
        
        # Add edges above threshold
        retained_edges = 0
        total_edges = len(edge_freq)
        
        for (src, tgt), freq in edge_freq.items():
            if freq >= threshold:
                dfg.add_edge(src, tgt)
                retained_edges += 1
        
        # Log filtering statistics
        retention_rate = retained_edges / total_edges if total_edges > 0 else 0
        logger.info(f"Edge filtering: {retained_edges}/{total_edges} retained ({retention_rate:.2%})")
        
        # Warning if filtering is too aggressive
        if retention_rate < 0.1 and total_edges > 5:
            logger.warning(f"Very aggressive filtering (only {retention_rate:.1%} edges retained). Consider lowering noise_threshold.")
        elif retention_rate > 0.9 and self.noise_threshold > 0.05:
            logger.debug(f"Minimal filtering applied ({retention_rate:.1%} edges retained)")
        
        # Preserve start/end information if available
        self._preserve_start_end_nodes(dfg, log)
        
        return dfg

    def _create_log_hash(self, log: Dict[Tuple[str, ...], int]) -> str:
        """
        Create a hash-based key for the log for efficient caching.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            The log to hash
            
        Returns:
        --------
        str
            A hash key representing the log content
        """
        # Create a stable string representation of the log
        log_str = str(sorted(log.items()))
        return hashlib.md5(log_str.encode()).hexdigest()

    def _compute_edge_frequencies(self, log: Dict[Tuple[str, ...], int]) -> Dict[Tuple[str, str], int]:
        """
        Compute directly-follows edge frequencies from the log.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log with traces and frequencies
            
        Returns:
        --------
        Dict[Tuple[str, str], int]
            Dictionary mapping edges to their frequencies
        """
        edge_freq: Dict[Tuple[str, str], int] = {}
        
        for trace, freq in log.items():
            if len(trace) < 2:
                continue  # Skip empty traces and single-activity traces
                
            # Count all directly-follows relations in this trace
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                edge_freq[edge] = edge_freq.get(edge, 0) + freq
                
        return edge_freq

    def _calculate_adaptive_threshold(self, edge_freq: Dict[Tuple[str, str], int]) -> float:
        """
        Calculate an adaptive threshold for edge filtering based on frequency distribution.
        
        Parameters:
        -----------
        edge_freq : Dict[Tuple[str, str], int]
            Edge frequencies
            
        Returns:
        --------
        float
            Calculated threshold for filtering
        """
        if not edge_freq:
            return 0.0
            
        frequencies = list(edge_freq.values())
        max_freq = max(frequencies)
        min_freq = min(frequencies)
        
        # If frequencies are very similar, be more conservative
        freq_range = max_freq - min_freq
        if freq_range < max_freq * 0.2:  # Less than 20% variation
            threshold = min_freq * (1.0 - self.noise_threshold * 0.5)
            logger.debug("Low frequency variation detected, using conservative threshold")
        else:
            # Standard threshold calculation
            threshold = max_freq * self.noise_threshold
            
        # Ensure threshold is reasonable
        threshold = max(threshold, 1.0)  # At least frequency of 1
        threshold = min(threshold, max_freq)  # Not higher than max frequency
        
        return threshold

    def _preserve_start_end_nodes(self, dfg: DFG, log: Dict[Tuple[str, ...], int]):
        """
        Preserve start and end node information in the DFG.
        
        Parameters:
        -----------
        dfg : DFG
            The DFG to update
        log : Dict[Tuple[str, ...], int]
            Original log for extracting start/end information
        """
        try:
            if hasattr(dfg, 'start_nodes') and hasattr(dfg, 'end_nodes'):
                start_nodes = {trace[0] for trace in log.keys() if trace}
                end_nodes = {trace[-1] for trace in log.keys() if trace}
                
                dfg.start_nodes = start_nodes
                dfg.end_nodes = end_nodes
                
                logger.debug(f"Preserved start nodes: {start_nodes}")
                logger.debug(f"Preserved end nodes: {end_nodes}")
                
        except Exception as e:
            logger.debug(f"Could not preserve start/end nodes: {e}")

    def get_noise_threshold(self) -> float:
        """
        Get the current noise threshold value.
        
        Returns:
        --------
        float
            Current noise threshold for edge filtering
        """
        return self.noise_threshold
        
    def set_noise_threshold(self, threshold: float):
        """
        Set the noise threshold value with validation.
        
        Parameters:
        -----------
        threshold : float
            New noise threshold value (0.0 - 1.0)
        """
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"Noise threshold must be between 0.0 and 1.0, got {threshold}")
        self.noise_threshold = threshold
        logger.debug(f"Noise threshold updated to {threshold}")
        
    def clear_cache(self):
        """Clear the internal caches to free memory."""
        self._edge_freq_cache.clear()
        self._log_stats_cache.clear()
        logger.debug("Caches cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about cache usage.
        
        Returns:
        --------
        Dict[str, int]
            Cache statistics including size and hit rates
        """
        return {
            'edge_freq_cache_size': len(self._edge_freq_cache),
            'log_stats_cache_size': len(self._log_stats_cache),
        }
