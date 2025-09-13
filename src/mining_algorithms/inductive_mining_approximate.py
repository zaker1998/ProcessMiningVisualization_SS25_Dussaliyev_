from typing import Dict, Tuple, Optional, List, Set
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
from logger import get_logger
from mining_algorithms.process_tree import ProcessTreeNode, Operator
from mining_algorithms.inductive_mining import InductiveMining
import hashlib
import time
from collections import OrderedDict

logger = get_logger("InductiveMiningApproximate")


class InductiveMiningApproximate(InductiveMining):
    """
    Approximate variant that attempts cuts on the full DFG, and if cut quality
    is poor, falls back to a simplified DFG where low-frequency edges are removed.
    
    Improvements:
    - Enhanced activity binning with better similarity metrics
    - Improved cut quality validation with adaptive thresholds
    - Better performance optimization and caching
    - Enhanced error handling and logging
    - More robust edge case handling
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        super().__init__(log)
        self.simplification_threshold = 0.1
        self.min_bin_freq = 0.2
        
        # Performance optimization caches - using OrderedDict for LRU behavior
        self._dfg_cache: OrderedDict[str, DFG] = OrderedDict()
        self._binning_cache: OrderedDict[str, Dict[Tuple[str, ...], int]] = OrderedDict()
        self._max_cache_size = 128

    def generate_graph(self, activity_threshold=0.0, traces_threshold=0.2, simplification_threshold=0.1, min_bin_freq=0.2):
        """
        Set simplification threshold, min_bin_freq and call parent generate_graph.
        
        Parameters:
        -----------
        activity_threshold : float
            Minimum frequency threshold for activities (0.0 - 1.0)
        traces_threshold : float
            Minimum frequency threshold for traces (0.0 - 1.0)
        simplification_threshold : float
            Threshold for DFG simplification (0.0 - 1.0)
        min_bin_freq : float
            Minimum frequency for activity binning (0.0 - 1.0)
        """
        # Validate parameters
        simplification_threshold = max(0.0, min(1.0, simplification_threshold))
        min_bin_freq = max(0.0, min(1.0, min_bin_freq))
        
        self.simplification_threshold = simplification_threshold
        self.min_bin_freq = min_bin_freq
        
        logger.info(f"Starting approximate mining with simplification_threshold={simplification_threshold}, min_bin_freq={min_bin_freq}")
        
        # Store original frequency map before any binning
        original_frequency_map = self._build_frequency_map()
        
        # Apply activity binning if min_bin_freq is set
        if self.min_bin_freq > 0.0:
            try:
                # Create binned log before processing
                binned_log = self._apply_activity_binning(self.log, min_bin_freq)
                
                if binned_log != self.log:
                    logger.info(f"Applied activity binning: {len(self.log)} -> {len(binned_log)} unique traces")
                    
                # Temporarily replace the log for processing
                original_log = self.log
                self.log = binned_log
                try:
                    super().generate_graph(activity_threshold, traces_threshold)
                    # Restore original frequency map for visualization
                    if hasattr(self, 'graph') and self.graph:
                        self.graph.frequency = original_frequency_map
                finally:
                    # Restore original log
                    self.log = original_log
                    
            except Exception as e:
                logger.error(f"Error in activity binning: {e}")
                # Fallback to processing without binning
                super().generate_graph(activity_threshold, traces_threshold)
        else:
            super().generate_graph(activity_threshold, traces_threshold)

    def _apply_activity_binning(self, log: Dict[Tuple[str, ...], int], min_bin_freq: float) -> Dict[Tuple[str, ...], int]:
        """
        Group activities with similar behavior patterns based on min_bin_freq threshold.
        
        Improved implementation with:
        - Better performance through caching
        - Enhanced similarity metrics
        - More robust edge case handling
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log
        min_bin_freq : float
            Minimum frequency threshold for binning
            
        Returns:
        --------
        Dict[Tuple[str, ...], int]
            Log with binned activities
        """
        if not log or min_bin_freq <= 0:
            return log
            
        # Create cache key
        cache_key = hashlib.md5(f"{sorted(log.items())}_{min_bin_freq}".encode()).hexdigest()
        
        # Check cache first (LRU behavior)
        if cache_key in self._binning_cache:
            logger.debug("Using cached binning result")
            # Move to end for LRU
            self._binning_cache.move_to_end(cache_key)
            return self._binning_cache[cache_key]
            
        start_time = time.time()
        
        try:
            # Calculate activity patterns with improved efficiency
            activity_stats = self._compute_activity_statistics(log)
            
            # Find activities to bin together
            activity_bins = self._find_activity_bins_improved(activity_stats, min_bin_freq)
            
            # Check if any meaningful binning occurred
            unique_representatives = len(set(activity_bins.values()))
            total_activities = len(activity_bins)
            
            if unique_representatives >= total_activities * 0.9:
                logger.debug("Minimal binning benefit detected, skipping")
                self._cache_binning_result(cache_key, log)
                return log
            
            # Create binned log
            binned_log = self._create_binned_log(log, activity_bins)
            
            # Cache the result
            self._cache_binning_result(cache_key, binned_log)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Activity binning completed in {elapsed_time:.3f}s: {total_activities} -> {unique_representatives} activities")
            
            return binned_log
            
        except Exception as e:
            logger.error(f"Error in activity binning: {e}")
            return log

    def _cache_binning_result(self, cache_key: str, result: Dict[Tuple[str, ...], int]):
        """Cache binning result with LRU eviction."""
        # Bound cache size with LRU eviction
        if len(self._binning_cache) >= self._max_cache_size:
            self._binning_cache.popitem(last=False)  # Remove oldest
        self._binning_cache[cache_key] = result

    def _compute_activity_statistics(self, log: Dict[Tuple[str, ...], int]) -> Dict[str, Dict]:
        """
        Compute comprehensive statistics for each activity.
        
        Returns:
        --------
        Dict[str, Dict]
            Statistics for each activity including frequency, predecessors, successors
        """
        activity_stats = {}
        
        for trace, freq in log.items():
            for i, activity in enumerate(trace):
                if activity not in activity_stats:
                    activity_stats[activity] = {
                        'frequency': 0,
                        'predecessors': {},
                        'successors': {},
                        'weighted_positions': [],  # Store (position, frequency) pairs
                        'trace_count': set()  # Use set to count unique traces
                    }
                
                stats = activity_stats[activity]
                stats['frequency'] += freq
                stats['trace_count'].add(trace)  # Count unique traces
                
                # Store weighted position
                relative_pos = i / len(trace) if len(trace) > 1 else 0.5
                stats['weighted_positions'].append((relative_pos, freq))
                
                # Update predecessors
                if i > 0:
                    pred = trace[i-1]
                    stats['predecessors'][pred] = stats['predecessors'].get(pred, 0) + freq
                
                # Update successors  
                if i < len(trace) - 1:
                    succ = trace[i+1]
                    stats['successors'][succ] = stats['successors'].get(succ, 0) + freq
        
        # Compute derived statistics
        for activity, stats in activity_stats.items():
            # Weighted average position in traces (0=start, 1=end)
            if stats['weighted_positions']:
                total_weight = sum(freq for _, freq in stats['weighted_positions'])
                weighted_sum = sum(pos * freq for pos, freq in stats['weighted_positions'])
                stats['avg_position'] = weighted_sum / total_weight if total_weight > 0 else 0.5
            else:
                stats['avg_position'] = 0.5
                
            # Convert trace_count set to actual count
            stats['trace_count'] = len(stats['trace_count'])
            
            # Variety of contexts (unique predecessors + successors)
            stats['context_variety'] = len(set(stats['predecessors'].keys()) | set(stats['successors'].keys()))
            
        return activity_stats

    def _find_activity_bins_improved(self, activity_stats: Dict[str, Dict], min_bin_freq: float) -> Dict[str, str]:
        """
        Find which activities should be binned together using improved similarity metrics.
        
        Returns a mapping: original_activity -> bin_representative
        """
        activities = list(activity_stats.keys())
        bins = {}
        
        if len(activities) <= 1:
            return {act: act for act in activities}
        
        # Calculate frequency threshold for minimum activity frequency
        max_freq = max(stats['frequency'] for stats in activity_stats.values()) if activity_stats else 1
        # Higher min_bin_freq should allow MORE activities to be considered (lower threshold)
        min_activity_freq = max_freq * (1.0 - min_bin_freq) * 0.1
        
        # Group activities by similarity
        processed = set()
        
        for activity in activities:
            if activity in processed:
                continue
                
            # Find similar activities using enhanced similarity
            similar_group = [activity]
            
            for other_activity in activities:
                if other_activity == activity or other_activity in processed:
                    continue
                
                if self._activities_similar_enhanced(
                    activity, other_activity, activity_stats, min_activity_freq, min_bin_freq
                ):
                    similar_group.append(other_activity)
            
            # Create bin with most frequent activity as representative
            if len(similar_group) > 1:
                representative = max(similar_group, key=lambda a: activity_stats[a]['frequency'])
                for act in similar_group:
                    bins[act] = representative
                    processed.add(act)
                logger.debug(f"Created bin with representative '{representative}' for activities: {similar_group}")
            else:
                bins[activity] = activity
                processed.add(activity)
        
        return bins

    def _activities_similar_enhanced(self, act1: str, act2: str, activity_stats: Dict[str, Dict], 
                                   min_activity_freq: float, similarity_threshold: float) -> bool:
        """
        Enhanced similarity check using multiple metrics.
        
        Parameters:
        -----------
        act1, act2 : str
            Activities to compare
        activity_stats : Dict[str, Dict]
            Precomputed activity statistics
        min_activity_freq : float
            Minimum activity frequency threshold
        similarity_threshold : float
            Overall similarity threshold for binning (higher values = more aggressive binning)
            
        Returns:
        --------
        bool
            True if activities are similar enough to bin together
        """
        stats1 = activity_stats[act1]
        stats2 = activity_stats[act2]
        
        freq1 = stats1['frequency']
        freq2 = stats2['frequency']
        
        # Skip if either activity is below minimum frequency threshold
        if freq1 < min_activity_freq or freq2 < min_activity_freq:
            return False
        
        # Convert similarity_threshold to actual threshold (invert for proper behavior)
        # Higher similarity_threshold (min_bin_freq) should mean MORE aggressive binning
        actual_threshold = 1.0 - similarity_threshold
        
        # Enhanced frequency similarity check with inverted threshold
        freq_ratio = min(freq1, freq2) / max(freq1, freq2) if max(freq1, freq2) > 0 else 0
        if freq_ratio < actual_threshold * 0.3:  # More aggressive frequency ratio check
            return False
        
        # Position similarity (activities that appear in similar positions)
        pos_diff = abs(stats1['avg_position'] - stats2['avg_position'])
        pos_similarity = 1.0 - pos_diff  # 1.0 = same position, 0.0 = opposite ends
        
        # Context similarity (predecessors and successors)
        pred1 = set(stats1['predecessors'].keys())
        pred2 = set(stats2['predecessors'].keys())
        pred_similarity = len(pred1 & pred2) / len(pred1 | pred2) if pred1 | pred2 else 1.0
        
        succ1 = set(stats1['successors'].keys())
        succ2 = set(stats2['successors'].keys())
        succ_similarity = len(succ1 & succ2) / len(succ1 | succ2) if succ1 | succ2 else 1.0
        
        # Context variety similarity (activities with similar complexity)
        var1 = stats1['context_variety']
        var2 = stats2['context_variety']
        variety_similarity = 1.0 - abs(var1 - var2) / max(var1 + var2, 1) if var1 + var2 > 0 else 1.0
        
        # Weighted overall similarity
        overall_similarity = (
            0.3 * pos_similarity +
            0.3 * pred_similarity +
            0.3 * succ_similarity +
            0.1 * variety_similarity
        )
        
        # Use inverted threshold for proper behavior (higher min_bin_freq = more aggressive binning)
        return overall_similarity >= actual_threshold

    def _create_binned_log(self, log: Dict[Tuple[str, ...], int], activity_bins: Dict[str, str]) -> Dict[Tuple[str, ...], int]:
        """
        Create a new log with binned activities.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Original log
        activity_bins : Dict[str, str]
            Mapping from activity to bin representative
            
        Returns:
        --------
        Dict[Tuple[str, ...], int]
            New log with binned activities
        """
        binned_log = {}
        
        for trace, freq in log.items():
            binned_trace = tuple(activity_bins.get(activity, activity) for activity in trace)
            binned_log[binned_trace] = binned_log.get(binned_trace, 0) + freq
        
        return binned_log

    def _create_filtered_log_for_dfg(self, log: Dict[Tuple[str, ...], int], dfg) -> Dict[Tuple[str, ...], int]:
        """
        Create a filtered log that only contains traces with edges present in the given DFG.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Original log
        dfg : DFG
            The DFG to use for filtering
            
        Returns:
        --------
        Dict[Tuple[str, ...], int]
            Filtered log matching the DFG structure
        """
        if not log or not dfg:
            return log
            
        # Get valid edges from DFG using the correct method
        try:
            valid_edges = dfg.get_edges()
            if not valid_edges:
                logger.warning("DFG has no edges, returning original log")
                return log
        except Exception as e:
            logger.warning(f"Could not get edges from DFG: {e}, returning original log")
            return log
            
        logger.debug(f"Filtering log based on {len(valid_edges)} valid edges: {valid_edges}")
        
        filtered_log = {}
        filtered_traces = 0
        
        for trace, freq in log.items():
            if len(trace) <= 1:
                # Single activity traces are always valid
                filtered_log[trace] = freq
                continue
                
            # Check if all edges in this trace exist in the DFG
            trace_valid = True
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                if edge not in valid_edges:
                    trace_valid = False
                    logger.debug(f"Trace {trace} filtered out due to missing edge: {edge}")
                    break
                    
            if trace_valid:
                filtered_log[trace] = freq
                logger.debug(f"Trace {trace} retained (all edges present)")
            else:
                filtered_traces += freq
                
        logger.info(f"Log filtering: {len(log)} -> {len(filtered_log)} trace variants, {filtered_traces} traces filtered out")
        
        # Don't be too aggressive with fallback - allow significant filtering
        total_freq_original = sum(log.values())
        total_freq_filtered = sum(filtered_log.values())
        retention_rate = total_freq_filtered / total_freq_original if total_freq_original > 0 else 0
        
        if retention_rate < 0.05:  # Only fallback if less than 5% of traces remain
            logger.warning(f"Filtering extremely aggressive ({retention_rate:.1%} retention), using original log")
            return log
        
        if not filtered_log:  # If no traces remain, use original
            logger.warning("No traces remain after filtering, using original log")
            return log
            
        return filtered_log

    def get_min_bin_freq(self) -> float:
        """
        Get the current minimum bin frequency value.
        
        Returns
        -------
        float
            The minimum bin frequency value for activity binning.
        """
        return self.min_bin_freq

    def set_min_bin_freq(self, min_bin_freq: float):
        """
        Set the minimum bin frequency value with validation.
        
        Parameters:
        -----------
        min_bin_freq : float
            New minimum bin frequency value (0.0 - 1.0)
        """
        if not (0.0 <= min_bin_freq <= 1.0):
            raise ValueError(f"min_bin_freq must be between 0.0 and 1.0, got {min_bin_freq}")
        self.min_bin_freq = min_bin_freq
        logger.debug(f"min_bin_freq updated to {min_bin_freq}")

    def calculate_cut(self, log):
        """
        Override calculate_cut with approximate strategy:
        1. Try user's specified simplification_threshold first (if > 0)
        2. Fallback to full DFG with quality validators
        3. Auto-tune small parameter grid as last resort
        
        Enhanced with better caching and error handling.
        """
        if not log:
            logger.debug("Empty log provided to calculate_cut")
            return None
            
        try:
            # Define cuts to try
            cuts_to_try = [
                ("xor", exclusive_cut, exclusive_split, self._validate_exclusive_cut_quality),
                ("seq", sequence_cut, sequence_split, self._validate_sequence_cut_quality),
                ("par", parallel_cut, parallel_split, self._validate_parallel_cut_quality),
                ("loop", loop_cut, loop_split, self._validate_loop_cut_quality)
            ]
            
            # FIRST: Try user's specified simplification_threshold if > 0 (SMART MODE)
            if self.simplification_threshold > 0:
                logger.debug(f"Using smart simplified mode with simplification_threshold={self.simplification_threshold}")
                simplified_dfg = self._get_cached_dfg(log, "simplified")
                
                # Check if simplified DFG is too sparse (would create flower model)
                original_edges = len(self._get_cached_dfg(log, "full").get_edges())
                simplified_edges = len(simplified_dfg.get_edges())
                retention_ratio = simplified_edges / original_edges if original_edges > 0 else 0
                
                if retention_ratio < 0.3:  # If less than 30% of edges remain
                    logger.warning(f"Simplified DFG too sparse ({retention_ratio:.1%} edges retained), using hybrid approach")
                    # Use a less aggressive threshold to avoid flower models
                    original_threshold = self.simplification_threshold
                    self.simplification_threshold = self.simplification_threshold * 0.5  # Halve the aggressiveness
                    simplified_dfg = self.create_simplified_dfg(log)  # Recreate with less aggressive threshold
                    self.simplification_threshold = original_threshold  # Restore original
                
                # Create filtered log that matches the simplified DFG
                filtered_log = self._create_filtered_log_for_dfg(log, simplified_dfg)
                
                # Try with quality validation first
                for cut_name, cut_func, split_func, validator in cuts_to_try:
                    try:
                        if partitions := cut_func(simplified_dfg):
                            # Use filtered log for splits to preserve simplification effect
                            splits = split_func(filtered_log, partitions)
                            # Use quality validator for user-specified threshold
                            if validator(splits, filtered_log):
                                logger.debug(f"Found quality {cut_name} cut with simplification_threshold={self.simplification_threshold}")
                                return (cut_name, splits)
                    except Exception as e:
                        logger.debug(f"Error trying {cut_name} cut on simplified DFG: {e}")
                        continue
                
                # If quality validation fails, try with relaxed validation (still on simplified DFG)
                for cut_name, cut_func, split_func, _ in cuts_to_try:
                    try:
                        if partitions := cut_func(simplified_dfg):
                            splits = split_func(filtered_log, partitions)
                            # Relaxed validation for simplified DFG
                            if self._strengthened_split_validation(splits, filtered_log):
                                logger.debug(f"Found {cut_name} cut on simplified DFG (relaxed validation)")
                                return (cut_name, splits)
                    except Exception as e:
                        logger.debug(f"Error trying {cut_name} cut on simplified DFG (relaxed): {e}")
                        continue
                
                # If simplified approach completely fails, try full DFG as fallback
                logger.warning("Simplified DFG failed to find cuts, trying full DFG as fallback")
                full_dfg = self._get_cached_dfg(log, "full")
                
                for cut_name, cut_func, split_func, validator in cuts_to_try:
                    try:
                        if partitions := cut_func(full_dfg):
                            splits = split_func(log, partitions)
                            if validator(splits, log):
                                logger.debug(f"Found {cut_name} cut on full DFG (fallback from failed simplification)")
                                return (cut_name, splits)
                    except Exception as e:
                        logger.debug(f"Error trying {cut_name} cut on full DFG (fallback): {e}")
                        continue
                
                logger.debug("No cuts found even with full DFG fallback")
                return None
            
            # SECOND: Standard full DFG mode (only when simplification_threshold = 0)
            logger.debug("Using full DFG mode (simplification_threshold = 0)")
            full_dfg = self._get_cached_dfg(log, "full")
            
            for cut_name, cut_func, split_func, validator in cuts_to_try:
                try:
                    if partitions := cut_func(full_dfg):
                        splits = split_func(log, partitions)
                        if validator(splits, log):
                            logger.debug(f"Found quality {cut_name} cut on full DFG")
                            return (cut_name, splits)
                except Exception as e:
                    logger.debug(f"Error trying {cut_name} cut: {e}")
                    continue
            
            # THIRD: Auto-tune as last resort (only if user hasn't set any parameters)
            if self.simplification_threshold <= 0 and self.min_bin_freq <= 0:
                logger.debug("Attempting auto-parameter suggestion as last resort")
                candidate_min_bin = [0.0, 0.1, 0.2, 0.3]
                candidate_simpl = [0.0, 0.05, 0.1, 0.2]
                
                for mb in candidate_min_bin:
                    try:
                        binned_log = self._apply_activity_binning(log, mb) if mb > 0.0 else log
                        # Log binning effect
                        if binned_log is not log:
                            uniq_acts = len({a for t in log for a in t})
                            uniq_acts_b = len({a for t in binned_log for a in t})
                            logger.debug(f"Auto binning: min_bin_freq={mb} activities {uniq_acts}->{uniq_acts_b}")
                        # Build full dfg on binned log first
                        dfg_full_b = DFG(binned_log)
                        for cut_name, cut_func, split_func, validator in cuts_to_try:
                            if partitions := cut_func(dfg_full_b):
                                splits = split_func(binned_log, partitions)
                                if self._strengthened_split_validation(splits, binned_log):
                                    logger.debug(f"Auto found {cut_name} cut on full DFG (min_bin_freq={mb})")
                                    return (cut_name, splits)
                        # Try simplified grids
                        for st in candidate_simpl:
                            prev = self.simplification_threshold
                            try:
                                self.simplification_threshold = st
                                dfg_s = self.create_simplified_dfg(binned_log)
                                for cut_name, cut_func, split_func, validator in cuts_to_try:
                                    if partitions := cut_func(dfg_s):
                                        splits = split_func(binned_log, partitions)
                                        if self._strengthened_split_validation(splits, binned_log):
                                            logger.debug(f"Auto found {cut_name} cut on simplified DFG (min_bin_freq={mb}, simpl={st})")
                                            return (cut_name, splits)
                            finally:
                                self.simplification_threshold = prev
                    except Exception as e:
                        logger.debug(f"Auto-tune iteration error (min_bin_freq={mb}): {e}")
                        continue
            
            logger.debug("No cuts found with current parameters - returning None")
            return None
            
        except Exception as e:
            logger.error(f"Error in calculate_cut: {e}")
            return None

    def _get_cached_dfg(self, log: Dict[Tuple[str, ...], int], dfg_type: str) -> DFG:
        """
        Get a cached DFG or create and cache a new one.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log
        dfg_type : str
            Type of DFG ("full" or "simplified")
            
        Returns:
        --------
        DFG
            Cached or newly created DFG
        """
        # Include simplification_threshold in cache key for simplified DFGs
        if dfg_type == "simplified":
            cache_key = f"{dfg_type}_{self.simplification_threshold}_{hashlib.sha1(str(sorted(log.items())).encode()).hexdigest()}"
        else:
            cache_key = f"{dfg_type}_{hashlib.sha1(str(sorted(log.items())).encode()).hexdigest()}"
        
        if cache_key in self._dfg_cache:
            logger.debug(f"Using cached {dfg_type} DFG")
            # Move to end for LRU
            self._dfg_cache.move_to_end(cache_key)
            return self._dfg_cache[cache_key]
        
        if dfg_type == "full":
            dfg = DFG(log)
        elif dfg_type == "simplified":
            dfg = self.create_simplified_dfg(log)
        else:
            raise ValueError(f"Unknown DFG type: {dfg_type}")
        
        # Bound cache size with LRU eviction
        if len(self._dfg_cache) >= self._max_cache_size:
            self._dfg_cache.popitem(last=False)  # Remove oldest
        self._dfg_cache[cache_key] = dfg
        return dfg

    def _strengthened_split_validation(self, splits: List[Dict], original_log: Dict[Tuple[str, ...], int]) -> bool:
        """
        Strengthened validation for splits that includes frequency preservation.
        
        Parameters:
        -----------
        splits : List[Dict]
            The splits produced by the cut
        original_log : Dict[Tuple[str, ...], int]
            Original log for frequency comparison
            
        Returns:
        --------
        bool
            True if splits pass strengthened validation
        """
        if not splits or len(splits) < 2:
            return False
        
        # Check that all splits are non-empty
        total_split_freq = 0
        for split in splits:
            if not split or sum(split.values()) == 0:
                return False
            total_split_freq += sum(split.values())
        
        # Check frequency preservation (should roughly match original)
        original_freq = sum(original_log.values()) if original_log else 0
        if original_freq > 0:
            preservation_ratio = total_split_freq / original_freq
            # More lenient threshold for approximate miner
            if preservation_ratio < 0.7:  # Allow 30% loss due to simplification
                logger.debug(f"Split frequency preservation too low: {preservation_ratio:.2%}")
                return False
        
        return True

    def create_simplified_dfg(self, log):
        """
        Simplify DFG by removing edges below simplification_threshold * max_edge_frequency.
        
        Enhanced with better error handling and logging.
        """
        if not log:
            return DFG()
            
        try:
            dfg = DFG(log)
            
            if self.simplification_threshold <= 0:
                logger.debug("Simplification threshold is 0, returning full DFG")
                return dfg

            # Compute edge frequencies
            edge_freq = {}
            for trace, f in log.items():
                if len(trace) < 2:
                    continue
                    
                for i in range(len(trace) - 1):
                    e = (trace[i], trace[i + 1])
                    edge_freq[e] = edge_freq.get(e, 0) + f

            if not edge_freq:
                logger.debug("No edges found for simplification")
                return dfg

            max_f = max(edge_freq.values())
            
            # Smart threshold calculation - be less aggressive at lower settings
            if self.simplification_threshold <= 0.1:
                # For low thresholds, only filter very weak edges
                threshold = max(1.0, max_f * self.simplification_threshold)
            else:
                # For higher thresholds, use standard calculation
                threshold = max_f * self.simplification_threshold
                
            logger.debug(f"Simplification: threshold={threshold} (max_freq={max_f}, simpl={self.simplification_threshold})")
            
            # Log edge frequencies for debugging
            logger.debug(f"Edge frequencies: {sorted(edge_freq.items(), key=lambda x: x[1], reverse=True)}")

            # Create simplified DFG
            simplified = DFG()
            
            # Add all nodes
            for node in dfg.get_nodes():
                simplified.add_node(node)
            
            # Add edges above threshold
            retained_edges = 0
            total_edges = len(edge_freq)
            filtered_edges = []
            
            for edge in dfg.get_edges():
                freq = edge_freq.get(edge, 0)
                if freq >= threshold:
                    simplified.add_edge(edge[0], edge[1])
                    retained_edges += 1
                    logger.debug(f"Retained edge {edge} (freq={freq} >= {threshold})")
                else:
                    filtered_edges.append((edge, freq))

            # Log simplification statistics
            retention_rate = retained_edges / total_edges if total_edges > 0 else 0
            logger.info(f"DFG simplification: {retained_edges}/{total_edges} edges retained ({retention_rate:.2%})")
            if filtered_edges:
                logger.debug(f"Filtered edges: {filtered_edges}")
            
            # Ensure we have enough structure left for meaningful process discovery
            if retention_rate < 0.2:  # Less than 20% edges retained
                logger.warning(f"Very sparse simplification ({retention_rate:.1%}), might produce flower model")
            
            # Ensure we maintain connectivity for main process paths
            start_nodes = simplified.get_start_nodes() if hasattr(simplified, 'get_start_nodes') else set()
            end_nodes = simplified.get_end_nodes() if hasattr(simplified, 'get_end_nodes') else set()
            
            if len(start_nodes) == 0 or len(end_nodes) == 0:
                logger.warning("Simplified DFG has no start/end nodes, might cause issues")

            # Ensure we preserve start/end nodes properly
            try:
                if hasattr(dfg, 'start_nodes') and hasattr(dfg, 'end_nodes'):
                    simplified.start_nodes = dfg.start_nodes.copy()
                    simplified.end_nodes = dfg.end_nodes.copy()
                    
                # Verify connectivity after simplification
                if simplified.start_nodes and simplified.end_nodes:
                    logger.debug(f"Preserved start nodes: {simplified.start_nodes}")
                    logger.debug(f"Preserved end nodes: {simplified.end_nodes}")
                else:
                    # Reconstruct start/end nodes from remaining edges
                    all_sources = {edge[0] for edge in simplified.get_edges()}
                    all_targets = {edge[1] for edge in simplified.get_edges()}
                    
                    # Start nodes are those that appear as sources but not as targets
                    potential_starts = all_sources - all_targets
                    # End nodes are those that appear as targets but not as sources  
                    potential_ends = all_targets - all_sources
                    
                    if potential_starts:
                        simplified.start_nodes = potential_starts
                        logger.debug(f"Reconstructed start nodes: {potential_starts}")
                    if potential_ends:
                        simplified.end_nodes = potential_ends
                        logger.debug(f"Reconstructed end nodes: {potential_ends}")
                        
            except Exception as e:
                logger.debug(f"Error preserving start/end nodes: {e}")
                # Continue without failing
                pass
                
            return simplified
            
        except Exception as e:
            logger.error(f"Error creating simplified DFG: {e}")
            return DFG()

    # Enhanced quality validators with adaptive thresholds
    def _validate_exclusive_cut_quality(self, splits, log):
        """Enhanced exclusive cut quality validation."""
        if len(splits) < 2:
            return False
            
        try:
            split_activities = [set(self.get_log_alphabet(s)) for s in splits]
            total_overlaps = 0.0
            comparisons = 0
            
            for i in range(len(split_activities)):
                for j in range(i + 1, len(split_activities)):
                    inter = len(split_activities[i].intersection(split_activities[j]))
                    uni = len(split_activities[i].union(split_activities[j]))
                    if uni > 0:
                        overlap_ratio = inter / uni
                        total_overlaps += overlap_ratio
                        comparisons += 1
            
            if comparisons == 0:
                return True
                
            avg_overlap = total_overlaps / comparisons
            # Adaptive threshold based on log complexity
            threshold = self.simplification_threshold * (1.0 + len(split_activities) * 0.1)
            return avg_overlap <= threshold
            
        except Exception as e:
            logger.debug(f"Error in exclusive cut validation: {e}")
            return False

    def _validate_sequence_cut_quality(self, splits, log):
        """Enhanced sequence cut quality validation."""
        if len(splits) < 2:
            return False
            
        try:
            correct = 0
            total = 0
            
            for trace, freq in log.items():
                if len(trace) < 2:
                    continue
                    
                total += freq
                split_positions = []
                
                # Find which split each activity belongs to
                for i, split in enumerate(splits):
                    split_activities = set(self.get_log_alphabet(split))
                    for j, activity in enumerate(trace):
                        if activity in split_activities:
                            split_positions.append((i, j))
                            break
                
                # Check if splits appear in sequence order
                if len(split_positions) >= 2:
                    ordered = all(split_positions[k][0] <= split_positions[k + 1][0] 
                                for k in range(len(split_positions) - 1))
                    if ordered:
                        correct += freq
            
            if total == 0:
                return True
                
            quality_ratio = correct / total
            # Adaptive threshold
            threshold = max(0.6, 1.0 - self.simplification_threshold * 2)
            return quality_ratio >= threshold
            
        except Exception as e:
            logger.debug(f"Error in sequence cut validation: {e}")
            return False

    def _validate_parallel_cut_quality(self, splits, log):
        """Enhanced parallel cut quality validation."""
        if len(splits) < 2:
            return False
            
        try:
            seen = set()
            overlap_threshold = max(0.2, self.simplification_threshold * 3)
            
            for split in splits:
                activities = set(self.get_log_alphabet(split))
                overlap = seen.intersection(activities)
                
                if overlap:
                    overlap_ratio = len(overlap) / len(activities) if activities else 0
                    if overlap_ratio > overlap_threshold:
                        return False
                        
                seen.update(activities)
            
            return True
            
        except Exception as e:
            logger.debug(f"Error in parallel cut validation: {e}")
            return False

    def _validate_loop_cut_quality(self, splits, log):
        """Enhanced loop cut quality validation."""
        if len(splits) != 2:
            return False
            
        try:
            body, redo = splits
            body_acts = set(self.get_log_alphabet(body))
            redo_acts = set(self.get_log_alphabet(redo))
            
            if not body_acts or not redo_acts:
                return False
            
            redo_ratio = len(redo_acts) / (len(body_acts) + len(redo_acts))
            # Adaptive threshold based on simplification setting
            max_ratio = 0.5 + self.simplification_threshold * 0.5
            
            return redo_ratio <= max_ratio
            
        except Exception as e:
            logger.debug(f"Error in loop cut validation: {e}")
            return False

    def clear_cache(self):
        """Clear all internal caches to free memory."""
        self._dfg_cache.clear()
        self._binning_cache.clear()
        logger.debug("All caches cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about cache usage.
        
        Returns:
        --------
        Dict[str, int]
            Cache statistics
        """
        return {
            'dfg_cache_size': len(self._dfg_cache),
            'binning_cache_size': len(self._binning_cache),
        }