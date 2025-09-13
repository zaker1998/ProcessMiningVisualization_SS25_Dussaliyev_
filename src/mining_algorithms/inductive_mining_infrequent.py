from typing import Dict, Tuple, Optional, List, Set
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
from logger import get_logger
from mining_algorithms.inductive_mining import InductiveMining
import hashlib
from collections import OrderedDict

logger = get_logger("InductiveMiningInfrequent")


class InductiveMiningInfrequent(InductiveMining):
    """
    Infrequent Inductive Miner:
    - First tries to find cuts on the full Directly-Follows Graph (DFG).
    - If no cut is found, falls back to a filtered DFG where low-frequency
      directly-follows relations are removed.
    
    Improvements:
    - Better caching mechanism using content hashes with LRU eviction
    - Improved edge filtering with adaptive thresholds
    - Enhanced error handling and validation
    - Better logging for debugging
    - Adaptive split quality validation based on noise level
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        super().__init__(log)
        self.noise_threshold: float = 0.2
        # Use hash-based caching with LRU eviction
        self._edge_freq_cache: OrderedDict[str, Dict[Tuple[str, str], int]] = OrderedDict()
        self._dfg_cache: OrderedDict[str, DFG] = OrderedDict()
        self._log_stats_cache: OrderedDict[str, Dict] = OrderedDict()
        # Soft bounds
        self._max_cache_size = 256

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
        Infrequent cut detection with proper log filtering:
        1. If noise_threshold > 0, filter the log to remove traces with noisy edges
        2. Run standard inductive mining on the filtered log
        
        Returns:
            (operator, [sublogs...]) if a cut is found, otherwise None.
        """
        if not log:
            logger.debug("Empty log provided to calculate_cut")
            return None
            
        # Step 1: If noise filtering enabled, filter the log itself
        if self.noise_threshold > 0.0:
            try:
                logger.debug(f"Filtering log with noise_threshold={self.noise_threshold}")
                filtered_log = self._create_filtered_log(log)
                
                if filtered_log and filtered_log != log:
                    logger.debug(f"Log filtered: {len(log)} -> {len(filtered_log)} traces")
                    # Try cuts on the filtered log using standard approach
                    filtered_dfg = DFG(filtered_log)
                    cut = self._try_cuts_on_dfg_simple(filtered_dfg, filtered_log)
                    if cut:
                        logger.debug(f"Found cut on filtered log: {cut[0]}")
                        return cut
                    else:
                        logger.debug("No cuts found on filtered log, falling back to full log")
                else:
                    logger.debug("Log filtering produced no changes, using full log")
            except Exception as e:
                logger.error(f"Error in log filtering: {e}")
        
        # Step 2: Try full log (standard approach or fallback)
        try:
            logger.debug("Using full log for cut detection")
            full_dfg = DFG(log)
            cut = self._try_cuts_on_dfg_simple(full_dfg, log)
            if cut:
                logger.debug(f"Found cut on full log: {cut[0]}")
                return cut
        except Exception as e:
            logger.warning(f"Error with full log: {e}")
        
        # No cuts found with either approach
        return None

    def _get_cached_filtered_dfg(self, log: Dict[Tuple[str, ...], int]) -> DFG:
        """Get cached filtered DFG or create and cache a new one."""
        log_hash = self._create_log_hash(log)
        cache_key = f"filtered_{self.noise_threshold}_{log_hash}"
        
        if cache_key in self._dfg_cache:
            logger.debug("Using cached filtered DFG")
            # Move to end for LRU
            self._dfg_cache.move_to_end(cache_key)
            return self._dfg_cache[cache_key]
        
        # Create filtered DFG
        dfg = self._create_filtered_dfg(log)
        
        # Bound cache size with LRU eviction
        if len(self._dfg_cache) >= self._max_cache_size:
            self._dfg_cache.popitem(last=False)  # Remove oldest
        self._dfg_cache[cache_key] = dfg
        return dfg

    def _try_cuts_on_dfg_simple(self, dfg: DFG, log: Dict[Tuple[str, ...], int]) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Simple cut detection using basic validation (like standard inductive mining).
        
        Returns:
            (operator, [sublogs...]) if successful, otherwise None.
        """
        if not dfg or not log:
            return None
            
        try:
            # Try cuts in standard order: exclusive, sequence, parallel, loop
            if partitions := exclusive_cut(dfg):
                splits = exclusive_split(log, partitions)
                if self._basic_split_validation(splits, log):
                    return "xor", splits
                    
            if partitions := sequence_cut(dfg):
                splits = sequence_split(log, partitions)
                if self._basic_split_validation(splits, log):
                    return "seq", splits
                    
            if partitions := parallel_cut(dfg):
                splits = parallel_split(log, partitions)
                if self._basic_split_validation(splits, log):
                    return "par", splits
                    
            if partitions := loop_cut(dfg):
                splits = loop_split(log, partitions)
                if self._basic_split_validation(splits, log):
                    return "loop", splits
                    
        except Exception as e:
            logger.error(f"Error trying cuts on DFG: {e}")
            
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
                if self._validate_split_quality_adaptive(splits, log, "xor"):
                    return "xor", splits
                    
            if partitions := sequence_cut(dfg):
                splits = sequence_split(log, partitions)
                if self._validate_split_quality_adaptive(splits, log, "seq"):
                    return "seq", splits
                    
            if partitions := parallel_cut(dfg):
                splits = parallel_split(log, partitions)
                if self._validate_split_quality_adaptive(splits, log, "par"):
                    return "par", splits
                    
            if partitions := loop_cut(dfg):
                splits = loop_split(log, partitions)
                if self._validate_split_quality_adaptive(splits, log, "loop"):
                    return "loop", splits
                    
        except Exception as e:
            logger.error(f"Error trying cuts on DFG: {e}")
            
        return None

    def _validate_split_quality_adaptive(self, splits: List[Dict], log: Dict[Tuple[str, ...], int], cut_type: str) -> bool:
        """
        Adaptive validation that adjusts thresholds based on noise level and log characteristics.
        
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
        split_sizes = []
        for split in splits:
            if not split:
                logger.debug(f"Empty split found in {cut_type} cut")
                return False
            split_freq = sum(split.values())
            if split_freq == 0:
                logger.debug(f"Zero frequency split found in {cut_type} cut")
                return False
            total_split_freq += split_freq
            split_sizes.append(split_freq)
            
        # Adaptive frequency preservation threshold based on noise level and log size
        original_freq = sum(log.values())
        log_size = len(log)
        
        # Base preservation threshold starts at 0.8, but adapts based on conditions
        base_threshold = 0.8
        
        # Adjust for noise level: higher noise allows more loss
        noise_adjustment = -self.noise_threshold * 0.3  # Up to 30% reduction for high noise
        
        # Adjust for log complexity: more complex logs allow more loss
        complexity_factor = min(log_size / 100, 0.2)  # Up to 20% reduction for complex logs
        complexity_adjustment = -complexity_factor
        
        # Adjust for cut type: some cuts naturally lose more frequency
        cut_adjustments = {
            "xor": 0.0,    # Exclusive choice should preserve well
            "seq": -0.05,  # Sequence may lose some due to ordering
            "par": -0.1,   # Parallel may lose more due to interleaving
            "loop": -0.15  # Loop cuts often lose the most frequency
        }
        cut_adjustment = cut_adjustments.get(cut_type, 0.0)
        
        # Calculate adaptive threshold
        adaptive_threshold = base_threshold + noise_adjustment + complexity_adjustment + cut_adjustment
        adaptive_threshold = max(0.5, min(0.9, adaptive_threshold))  # Clamp to reasonable range
        
        if total_split_freq < original_freq * adaptive_threshold:
            logger.debug(f"Split frequency preservation below adaptive threshold: "
                        f"{total_split_freq/original_freq:.2%} < {adaptive_threshold:.2%} "
                        f"(noise={self.noise_threshold}, cut={cut_type})")
            return False
        
        # Check for balanced splits (avoid highly imbalanced decompositions)
        if len(split_sizes) > 1:
            max_split = max(split_sizes)
            min_split = min(split_sizes)
            if max_split > 0 and min_split / max_split < 0.05:  # One split has <5% of the largest
                logger.debug(f"Highly imbalanced split detected in {cut_type} cut")
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
        - Connectivity-aware filtering
        """
        if not log:
            logger.debug("Empty log provided to _create_filtered_dfg")
            return DFG()
        
        # Create hash-based cache key for better performance
        log_hash = self._create_log_hash(log)
        
        # Check cache first (LRU behavior)
        if log_hash in self._edge_freq_cache:
            edge_freq = self._edge_freq_cache[log_hash]
            logger.debug("Using cached edge frequencies")
            # Move to end for LRU
            self._edge_freq_cache.move_to_end(log_hash)
        else:
            # Compute edge frequencies
            edge_freq = self._compute_edge_frequencies(log)
            # Bound cache size with LRU eviction
            if len(self._edge_freq_cache) >= self._max_cache_size:
                self._edge_freq_cache.popitem(last=False)  # Remove oldest
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
        
        # Calculate adaptive threshold with connectivity awareness
        threshold = self._calculate_adaptive_threshold_with_connectivity(edge_freq, activities)
        logger.debug(f"Using edge frequency threshold: {threshold}")
        
        # Add edges above threshold
        retained_edges = 0
        total_edges = len(edge_freq)
        
        for (src, tgt), freq in edge_freq.items():
            if freq >= threshold:
                dfg.add_edge(src, tgt)
                retained_edges += 1
        
        # Only ensure minimal connectivity if we filtered out ALL edges (extreme case)
        if retained_edges == 0 and edge_freq:
            logger.warning("All edges filtered out, adding back strongest edge for minimal connectivity")
            # Add back just the strongest edge to avoid completely empty graph
            strongest_edge = max(edge_freq.items(), key=lambda x: x[1])
            dfg.add_edge(strongest_edge[0][0], strongest_edge[0][1])
            retained_edges = 1
        
        # Log filtering statistics
        retention_rate = retained_edges / total_edges if total_edges > 0 else 0
        logger.info(f"Edge filtering: {retained_edges}/{total_edges} retained ({retention_rate:.2%})")
        
        # Warning if filtering is too aggressive or too lenient
        if retention_rate < 0.1 and total_edges > 5:
            logger.warning(f"Very aggressive filtering (only {retention_rate:.1%} edges retained). Consider lowering noise_threshold.")
        elif retention_rate > 0.9 and self.noise_threshold > 0.05:
            logger.debug(f"Minimal filtering applied ({retention_rate:.1%} edges retained)")
        
        # Preserve start/end information if available
        self._preserve_start_end_nodes(dfg, log)
        
        return dfg

    def _create_filtered_log(self, log: Dict[Tuple[str, ...], int]) -> Dict[Tuple[str, ...], int]:
        """
        Create a filtered log by removing traces that contain edges filtered out by noise threshold.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Original log
            
        Returns:
        --------
        Dict[Tuple[str, ...], int]
            Log with noisy traces filtered out
        """
        if not log or self.noise_threshold <= 0.0:
            return log
            
        # Get edge frequencies and determine which edges to filter
        edge_freq = self._compute_edge_frequencies(log)
        if not edge_freq:
            return log
            
        activities = self.get_log_alphabet(log)
        threshold = self._calculate_adaptive_threshold_with_connectivity(edge_freq, activities)
        
        logger.debug(f"Edge frequencies: {edge_freq}")
        logger.debug(f"Calculated threshold: {threshold}")
        
        # Get set of edges that should be filtered out (below threshold)
        filtered_edges = set()
        for edge, freq in edge_freq.items():
            if freq < threshold:
                filtered_edges.add(edge)
        
        if not filtered_edges:
            logger.debug("No edges to filter, returning original log")
            return log
            
        logger.debug(f"Filtering out edges: {filtered_edges}")
        
        # Filter traces that contain any filtered edges
        filtered_log = {}
        for trace, freq in log.items():
            # Check if this trace contains any filtered edges
            contains_filtered_edge = False
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                if edge in filtered_edges:
                    contains_filtered_edge = True
                    break
            
            # Keep trace only if it doesn't contain filtered edges
            if not contains_filtered_edge:
                filtered_log[trace] = freq
            else:
                logger.debug(f"Filtered out trace: {' -> '.join(trace)} (freq: {freq})")
        
        return filtered_log

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
        return hashlib.sha1(log_str.encode()).hexdigest()

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

    def _calculate_adaptive_threshold_with_connectivity(self, edge_freq: Dict[Tuple[str, str], int], activities: Set[str]) -> float:
        """
        Calculate threshold that respects user's noise_threshold setting.
        
        Parameters:
        -----------
        edge_freq : Dict[Tuple[str, str], int]
            Edge frequencies
        activities : Set[str]
            Set of activities in the log
            
        Returns:
        --------
        float
            Calculated threshold for filtering
        """
        if not edge_freq:
            return 0.0
            
        frequencies = list(edge_freq.values())
        max_freq = max(frequencies)
        
        # PM4Py-style threshold: more aggressive filtering at higher thresholds
        if self.noise_threshold == 0.0:
            return 0.0  # No filtering
        
        # Calculate base threshold
        base_threshold = max_freq * self.noise_threshold
        
        # For very low thresholds (< 0.05), use a minimum of 1 to filter only single occurrences
        if self.noise_threshold < 0.05:
            threshold = max(base_threshold, 1.0)
        else:
            threshold = base_threshold
        
        # Ensure reasonable bounds
        threshold = max(threshold, 0.0)
        threshold = min(threshold, max_freq - 1)  # Always keep at least the strongest edge
        
        logger.debug(f"Noise threshold {self.noise_threshold} -> frequency threshold {threshold} (max_freq: {max_freq})")
        
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
        self._dfg_cache.clear()
        self._log_stats_cache.clear()
        logger.debug("Caches cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about cache usage.
        
        Returns:
        --------
        Dict[str, int]
            Cache statistics including all cache types
        """
        return {
            'edge_freq_cache_size': len(self._edge_freq_cache),
            'dfg_cache_size': len(self._dfg_cache),
            'log_stats_cache_size': len(self._log_stats_cache),
        }
