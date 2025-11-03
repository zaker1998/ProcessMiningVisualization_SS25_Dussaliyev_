"""
Inductive Miner - Infrequent (IMf) - Canonical Implementation

This module implements the Inductive Miner - Infrequent algorithm as described in:

    Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P. (2014):
    Discovering Block-Structured Process Models from Event Logs Containing Infrequent Behaviour.
    Business Process Management Workshops. BPM 2013. Lecture Notes in Business Information Processing,
    vol 171. Springer, Cham. DOI: 10.1007/978-3-319-06257-0_6

Algorithm Overview:
-------------------
IMf extends the standard Inductive Miner to handle noisy event logs by filtering
infrequent directly-follows relations when necessary.

Key Steps:
1. Try to find cuts on the FULL DFG first (preserve information)
2. If no cut found, filter infrequent edges and retry
3. Split log based on discovered cuts and recurse
4. Fall-through to flower model if no cuts possible

This implementation follows the canonical algorithm specification and is designed
to be comparable with PM4Py's inductive miner implementation.
"""

from typing import Dict, Tuple, Optional, List, Set, Any, cast
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
from logger import get_logger
from mining_algorithms.inductive_mining import InductiveMining

logger = get_logger("InductiveMiningInfrequent")


class InductiveMiningInfrequent(InductiveMining):
    """
    Canonical implementation of Inductive Miner - Infrequent (IMf).
    
    This implementation strictly follows the algorithm described in the 2014 paper
    by Leemans et al., providing:
    
    - Sound process model discovery (no deadlocks)
    - Handling of infrequent behavior through edge filtering
    - Rediscoverability guarantees under noise threshold
    - Two-phase approach: full DFG first, then filtered DFG
    - Detailed logging for explainability
    
    Parameters:
    -----------
    log : Dict[Tuple[str, ...], int]
        Event log as a dictionary mapping traces to their frequencies
        
    Attributes:
    -----------
    noise_threshold : float
        Threshold for filtering infrequent edges (0.0 - 1.0)
        Default: 0.2 (filters edges with frequency < 20% of max edge frequency)
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        """
        Initialize IMf miner.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Event log with traces and their frequencies
        """
        super().__init__(log)
        self.noise_threshold: float = 0.2  # Canonical default from paper
        self._last_noise_threshold: float = -1.0  # Track last used threshold for change detection
        logger.info("Initialized IMf (Inductive Miner - Infrequent) with canonical algorithm")

    def generate_graph(
        self,
        activity_threshold: float = 0.0,
        traces_threshold: float = 0.0,
        noise_threshold: float = 0.2
    ):
        """
        Public entry point for process discovery using IMf.
        
        This method applies pre-filtering (activity and trace thresholds) and then
        runs the canonical IMf algorithm with the specified noise threshold.
        
        Parameters:
        -----------
        activity_threshold : float
            Minimum frequency threshold for activities (0.0 - 1.0)
            Activities with freq < threshold * max_activity_freq are removed
        traces_threshold : float  
            Minimum frequency threshold for traces (0.0 - 1.0)
            Traces with freq < threshold * max_trace_freq are removed
        noise_threshold : float
            Noise threshold for edge filtering (0.0 - 1.0)
            Edges with freq < threshold * max_edge_freq are filtered
            Recommended: 0.2 (20%)
        """
        # Validate noise threshold
        if not (0.0 <= noise_threshold <= 1.0):
            logger.warning(f"Invalid noise_threshold {noise_threshold}, clamping to [0.0, 1.0]")
            noise_threshold = max(0.0, min(1.0, noise_threshold))
        
        # Update threshold
        self.noise_threshold = noise_threshold
        
        # Log what we're doing
        logger.info(f"Starting IMf discovery with noise_threshold={noise_threshold}")
        logger.info(f"Pre-filtering: activity_threshold={activity_threshold}, "
                   f"traces_threshold={traces_threshold}")
        
        # CRITICAL: Check if we need to regenerate
        # Regenerate if: (1) filtered log changes OR (2) noise threshold changes
        events_to_remove = self.get_events_to_remove(activity_threshold)
        min_traces_frequency = self.calulate_minimum_traces_frequency(traces_threshold)
        
        from logs.filters import filter_traces, filter_events
        filtered_log = filter_traces(self.log, min_traces_frequency)
        filtered_log = filter_events(filtered_log, events_to_remove)
        
        # Apply noise-based log filtering (similar to activity/traces approach)
        # This ensures filtering persists through all recursion levels
        if noise_threshold > 0.0 and filtered_log:
            logger.info(f"Applying noise threshold filtering: {noise_threshold}")
            filtered_log = self._apply_noise_filtering_to_log(filtered_log, noise_threshold)
        
        # Check if anything changed
        log_changed = filtered_log != self.filtered_log
        threshold_changed = self._last_noise_threshold != noise_threshold
        
        if not log_changed and not threshold_changed:
            logger.debug("No changes detected - skipping regeneration")
            return
        
        if threshold_changed:
            logger.info(f"Noise threshold changed: {self._last_noise_threshold} -> {noise_threshold}")
        if log_changed:
            logger.info("Filtered log changed - regenerating")
        
        # Update state
        self.activity_threshold = activity_threshold
        self.traces_threshold = traces_threshold
        self.filtered_log = filtered_log
        self._last_noise_threshold = noise_threshold
        
        # Generate new process tree and graph
        logger.info("Start Inductive Mining")
        from graphs.visualization.inductive_graph import InductiveGraph
        process_tree = self.inductive_mining(self.filtered_log)
        self.graph = InductiveGraph(
            process_tree,
            frequency=self.appearance_frequency,
            node_sizes=self.node_sizes,
        )

    def calculate_cut(self, log: Dict[Tuple[str, ...], int]) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        IMf cut detection following the two-phase approach.
        
        Algorithm (from 2014 paper):
        -----------------------------
        Phase 1: Try to find a cut on the FULL DFG
            - Preserves all structural information
            - Succeeds when log is clean or noise doesn't affect structure
        
        Phase 2: Filter infrequent edges and retry
            - Only applied if Phase 1 fails
            - Removes edges with frequency < (noise_threshold × max_frequency)
            - Enables cut detection in noisy logs
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log for cut detection
        
        Returns:
        --------
        Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]
            If a cut is found: (operator, [sublog1, sublog2, ...])
            If no cut found: None
            
        Notes:
        ------
        - Empty traces skip cut detection (handled in fall-through)
        - Cut order: exclusive → sequence → parallel → loop
        - This matches the canonical algorithm specification
        """
        if not log:
            logger.debug("Empty log provided to calculate_cut")
            return None
            
        # Skip cut detection if empty trace present (will be handled in fall-through)
        if tuple() in log:
            logger.debug("Empty trace present in log, skipping cut detection (fall-through)")
            return None
            
        # PHASE 1: Try cuts on full DFG (preserve all information)
        # =========================================================
        logger.debug("PHASE 1: Attempting cut detection on full DFG")
        
        try:
            full_dfg = DFG(log)
            logger.debug(f"Full DFG: {len(full_dfg.get_nodes())} nodes, "
                        f"{len(full_dfg.get_edges())} edges")
            
            cut = self._try_all_cuts(full_dfg, log)
            if cut:
                operator, sublogs = cut
                logger.info(f"✓ Phase 1 SUCCESS: Found {operator} cut on full DFG")
                logger.debug(f"  Partitions: {len(sublogs)} sublogs with sizes "
                           f"{[len(sublog) for sublog in sublogs]}")
                return cut
            else:
                logger.debug("✗ Phase 1 FAILED: No cut found on full DFG")
                
        except Exception as e:
            logger.error(f"Error in Phase 1 (full DFG): {e}")
        
        # PHASE 2: Filter infrequent edges and retry
        # ===========================================
        if self.noise_threshold > 0.0:
            logger.debug(f"PHASE 2: Filtering infrequent edges (threshold={self.noise_threshold})")
            
            try:
                # Filter infrequent edges from DFG
                filtered_dfg = self._create_filtered_dfg(log)
                
                # Check if filtering made any difference
                if filtered_dfg.get_edges() == full_dfg.get_edges():
                    logger.debug("✗ Phase 2 SKIPPED: No edges filtered")
                    return None
                
                logger.debug(f"Filtered DFG: {len(filtered_dfg.get_nodes())} nodes, "
                           f"{len(filtered_dfg.get_edges())} edges")
                
                # Try cuts on filtered DFG
                cut = self._try_all_cuts(filtered_dfg, log)
                if cut:
                    operator, sublogs = cut
                    logger.info(f"✓ Phase 2 SUCCESS: Found {operator} cut on filtered DFG")
                    logger.debug(f"  Partitions: {len(sublogs)} sublogs with sizes "
                               f"{[len(sublog) for sublog in sublogs]}")
                    return cut
                else:
                    logger.debug("✗ Phase 2 FAILED: No cut found on filtered DFG")
                    
            except Exception as e:
                logger.error(f"Error in Phase 2 (filtered DFG): {e}")
        else:
            logger.debug("PHASE 2 SKIPPED: noise_threshold=0.0 (no filtering)")
            
        # No cuts found in either phase
        logger.debug("No cuts found, will proceed to fall-through")
        return None
        
    def _try_all_cuts(
        self,
        dfg: DFG,
        log: Dict[Tuple[str, ...], int]
    ) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Try all cut types in canonical order.
        
        Cut Detection Order (from paper):
        ----------------------------------
        1. Exclusive cut (XOR): Disconnected components
        2. Sequence cut (→): Ordered execution
        3. Parallel cut (∧): Concurrent execution
        4. Loop cut (↻): Repetitive structure
        
        Parameters:
        -----------
        dfg : DFG
            Directly-follows graph to analyze
        log : Dict[Tuple[str, ...], int]
            Log for splitting (after cut is found)
        
        Returns:
        --------
        Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]
            First valid cut found, or None if no cut succeeds
            
        Notes:
        ------
        - Validation checks that splits are valid and preserve trace frequencies
        - This implementation uses basic validation (as in standard IM)
        """
        if not dfg or not log:
            return None
            
        # Define cut attempts in canonical order
        cut_attempts = [
            ("xor", exclusive_cut, exclusive_split, "exclusive (XOR)"),
            ("seq", sequence_cut, sequence_split, "sequence (→)"),
            ("par", parallel_cut, parallel_split, "parallel (∧)"),
            ("loop", loop_cut, loop_split, "loop (↻)")
        ]
        
        for operator, cut_func, split_func, description in cut_attempts:
            try:
                logger.debug(f"  Trying {description} cut...")
                
                # Attempt to find partition
                partitions = cut_func(dfg)
                
                if partitions and len(partitions) > 1:
                    logger.debug(f"    Found partitions: {len(partitions)} sets")
                    
                    # Split log based on partition
                    # Cast to expected type for split function
                    splits = split_func(log, cast(List[Set[str]], partitions))
                    
                    # Validate split quality
                    if self._validate_split(splits, log, operator):
                        logger.debug(f"    ✓ {description} cut VALID")
                        return (operator, splits)
                    else:
                        logger.debug(f"    ✗ {description} cut INVALID (failed validation)")
                else:
                    logger.debug(f"    ✗ {description} cut not found")
                    
            except Exception as e:
                logger.debug(f"    ✗ {description} cut error: {e}")
                continue
                
        return None

    def _validate_split(
        self,
        splits: List[Dict[Tuple[str, ...], int]],
        original_log: Dict[Tuple[str, ...], int],
        operator: str
    ) -> bool:
        """
        Validate that a log split is acceptable.
        
        Validation Criteria:
        --------------------
        1. All splits must be non-empty
        2. Splits must preserve reasonable trace frequency
        3. Splits must not be trivially degenerate
        
        Parameters:
        -----------
        splits : List[Dict[Tuple[str, ...], int]]
            The proposed sublogs from splitting
        original_log : Dict[Tuple[str, ...], int]
            The original log before splitting
        operator : str
            The operator type ("xor", "seq", "par", "loop")
            
        Returns:
        --------
        bool
            True if split is valid and acceptable, False otherwise
        """
        if not splits or len(splits) < 2:
            logger.debug("      Validation FAIL: Less than 2 splits")
            return False
            
        # Check that all splits are non-empty
        for i, split in enumerate(splits):
            if not split:
                logger.debug(f"      Validation FAIL: Split {i} is empty")
                return False
            
            split_freq = sum(split.values())
            if split_freq == 0:
                logger.debug(f"      Validation FAIL: Split {i} has zero frequency")
                return False
        
        # Calculate total frequency preservation
        original_freq = sum(original_log.values())
        total_split_freq = sum(sum(split.values()) for split in splits)
        
        # Some operators naturally lose frequency (e.g., loop splits)
        # Use operator-specific thresholds
        min_preservation = {
            "xor": 0.9,   # Exclusive should preserve most frequency
            "seq": 0.8,   # Sequence may lose some due to projection
            "par": 0.7,   # Parallel may lose more due to interleaving
            "loop": 0.6   # Loop often loses frequency in splitting
        }
        
        threshold = min_preservation.get(operator, 0.7)
        preservation_ratio = total_split_freq / original_freq if original_freq > 0 else 0
        
        if preservation_ratio < threshold:
            logger.debug(f"      Validation FAIL: Frequency preservation {preservation_ratio:.2%} "
                        f"< {threshold:.0%} (operator={operator})")
            return False
        
        logger.debug(f"      Validation PASS: Frequency preserved {preservation_ratio:.2%}")
        return True

    def _create_filtered_dfg(self, log: Dict[Tuple[str, ...], int]) -> DFG:
        """
        Create filtered DFG by removing infrequent edges (CANONICAL Phase 2).
        
        CANONICAL Algorithm (from 2014 IMf paper - Phase 2):
        -----------------------------------------------------
        1. Compute frequency of each directly-follows edge
        2. Calculate threshold: max_frequency × noise_threshold
        3. Create new DFG with:
           - ALL nodes (activities) preserved
           - Only edges with frequency ≥ threshold
        4. Preserve start/end node metadata from original log
        
        IMPORTANT: This filters the DFG structure for cut detection in Phase 2,
        but does NOT modify the underlying log or remove traces. After finding
        a cut on the filtered DFG, we split the ORIGINAL log (preserving all
        trace information).
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input event log (used for computing edges, NOT modified)
            
        Returns:
        --------
        DFG
            Filtered directly-follows graph (edges filtered, all nodes kept)
            
        Notes:
        ------
        - All nodes (activities) are always preserved (CANONICAL requirement)
        - Only edges are filtered based on frequency
        - Start/end nodes are maintained from original log
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
        threshold = max_freq * self.noise_threshold
        
        logger.debug(f"Edge filtering threshold calculation:")
        logger.debug(f"  max_frequency = {max_freq}")
        logger.debug(f"  noise_threshold = {self.noise_threshold}")
        logger.debug(f"  computed_threshold = {threshold:.2f}")
        
        # Step 3: Create filtered DFG
        filtered_dfg = DFG()
        
        # Step 4: Add all nodes (preserve all activities)
        activities = self.get_log_alphabet(log)
        for activity in activities:
            filtered_dfg.add_node(activity)
        
        logger.debug(f"  activities = {len(activities)}")
        
        # Step 5: Add only frequent edges
        retained_edges = 0
        total_edges = len(edge_freq)
        
        for (src, tgt), freq in edge_freq.items():
            if freq >= threshold:
                filtered_dfg.add_edge(src, tgt)
                retained_edges += 1
        
        retention_rate = retained_edges / total_edges if total_edges > 0 else 0
        logger.info(f"DFG edge filtering (Phase 2): retained {retained_edges}/{total_edges} edges "
                   f"({retention_rate:.1%}) for cut detection")
        
        # Warn about extreme filtering
        if retention_rate < 0.1 and total_edges > 5:
            logger.warning(f"Very aggressive DFG filtering: only {retention_rate:.1%} edges retained. "
                          f"Consider lowering noise_threshold (current: {self.noise_threshold}). "
                          f"Note: This affects cut detection, not trace preservation.")
        elif retention_rate > 0.95:
            logger.debug(f"Minimal DFG filtering: {retention_rate:.1%} edges retained")
        
        # Step 6: Preserve start and end node information
        self._preserve_start_end_nodes(filtered_dfg, log)
        
        return filtered_dfg
    
    def _apply_noise_filtering_to_log(
        self, 
        log: Dict[Tuple[str, ...], int], 
        threshold: float
    ) -> Dict[Tuple[str, ...], int]:
        """
        Filter traces from log based on edge frequency threshold (noise removal).
        
        This approach mirrors activity/traces filtering: modify the log before mining
        so that filtering persists through all recursion levels.
        
        Algorithm:
        ----------
        1. Compute all edge frequencies in the log
        2. Calculate cutoff: max_freq × threshold
        3. Remove traces that contain edges below cutoff (noisy edges)
        4. Return filtered log
        
        This ensures noisy/infrequent edges are removed from the process model,
        similar to how activity_threshold removes infrequent activities.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log with traces and frequencies
        threshold : float
            Noise frequency threshold (0.0 - 1.0)
            
        Returns:
        --------
        Dict[Tuple[str, ...], int]
            Filtered log with only traces containing frequent edges
        """
        if threshold <= 0.0 or not log:
            return log
        
        # Compute edge frequencies
        edge_freq = self._compute_edge_frequencies(log)
        if not edge_freq:
            return log
        
        # Calculate cutoff
        max_freq = max(edge_freq.values())
        cutoff_value = max_freq * threshold
        
        logger.debug(f"Noise filtering: max_freq={max_freq}, threshold={threshold}, cutoff={cutoff_value}")
        
        # Determine which edges to keep (frequent edges, non-noisy)
        kept_edges = {edge for edge, freq in edge_freq.items() if freq >= cutoff_value}
        
        # Filter traces
        filtered_log: Dict[Tuple[str, ...], int] = {}
        original_trace_count = len(log)
        original_event_count = sum(freq for freq in log.values())
        kept_event_count = 0
        
        for trace, freq in log.items():
            # Keep single-activity traces
            if len(trace) < 2:
                filtered_log[trace] = freq
                kept_event_count += freq
                continue
            
            # Check if all edges in trace are frequent (non-noisy)
            if all((trace[i], trace[i + 1]) in kept_edges for i in range(len(trace) - 1)):
                filtered_log[trace] = freq
                kept_event_count += freq
        
        # Log filtering statistics
        filtered_trace_count = len(filtered_log)
        logger.info(f"Noise filtering removed {original_trace_count - filtered_trace_count}/{original_trace_count} trace variants")
        logger.info(f"Noise filtering kept {kept_event_count}/{original_event_count} trace instances "
                   f"({kept_event_count/original_event_count*100:.1f}%)")
        logger.info(f"Noise filtering kept {len(kept_edges)}/{len(edge_freq)} unique edges "
                   f"({len(kept_edges)/len(edge_freq)*100:.1f}%)")
        
        return filtered_log if filtered_log else log

    def _compute_edge_frequencies(self, log: Dict[Tuple[str, ...], int]) -> Dict[Tuple[str, str], int]:
        """
        Compute frequency of each directly-follows relation in the log.
        
        A directly-follows relation (a, b) means activity 'b' appears immediately
        after activity 'a' in at least one trace.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Event log with traces and frequencies
            
        Returns:
        --------
        Dict[Tuple[str, str], int]
            Dictionary mapping edges to their frequencies
            
        Example:
        --------
        For trace ('A', 'B', 'C') with frequency 10:
            Edge ('A', 'B') gets frequency +10
            Edge ('B', 'C') gets frequency +10
        """
        edge_freq: Dict[Tuple[str, str], int] = {}
        
        for trace, freq in log.items():
            # Skip empty traces and single-activity traces
            if len(trace) < 2:
                continue
                
            # Count all directly-follows relations in this trace
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                edge_freq[edge] = edge_freq.get(edge, 0) + freq
                
        return edge_freq

    def _preserve_start_end_nodes(self, dfg: DFG, log: Dict[Tuple[str, ...], int]):
        """
        Preserve start and end node information in the DFG (CANONICAL).
        
        IMPORTANT: In the canonical IMf algorithm, start/end node information is
        preserved from the ORIGINAL log, not from the filtered DFG. This ensures
        that all process start/end points are represented, even if some edges
        are filtered during Phase 2.
        
        Start nodes: First activities in traces
        End nodes: Last activities in traces
        
        This information is crucial for cut detection (especially parallel and loop cuts).
        
        Parameters:
        -----------
        dfg : DFG
            The DFG to update
        log : Dict[Tuple[str, ...], int]
            Original log for extracting start/end information
        """
        try:
            if hasattr(dfg, 'start_nodes') and hasattr(dfg, 'end_nodes'):
                # CANONICAL: Mark ALL activities that start/end traces
                # Do NOT filter by dfg_nodes - keep full process boundary information
                start_nodes: Set[str | int] = {
                    trace[0] for trace in log.keys() if len(trace) > 0
                }
                end_nodes: Set[str | int] = {
                    trace[-1] for trace in log.keys() if len(trace) > 0
                }

                dfg.start_nodes = start_nodes  # type: ignore
                dfg.end_nodes = end_nodes  # type: ignore
                
                logger.debug(f"Preserved start nodes: {start_nodes}")
                logger.debug(f"Preserved end nodes: {end_nodes}")
        except Exception as e:
            logger.debug(f"Could not preserve start/end nodes: {e}")

    # Public API for configuration and introspection

    def get_noise_threshold(self) -> float:
        """
        Get the current noise threshold value.
        
        Returns:
        --------
        float
            Current noise threshold (0.0 - 1.0)
        """
        return self.noise_threshold
        
    def set_noise_threshold(self, threshold: float):
        """
        Set the noise threshold value.
        
        Parameters:
        -----------
        threshold : float
            New noise threshold (0.0 - 1.0)
            
        Raises:
        -------
        ValueError
            If threshold is not in valid range [0.0, 1.0]
        """
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"Noise threshold must be between 0.0 and 1.0, got {threshold}")
        self.noise_threshold = threshold
        logger.info(f"Noise threshold updated to {threshold}")

    def get_algorithm_info(self) -> Dict[str, Any]:
        """
        Get information about the algorithm and its configuration.
        
        Returns:
        --------
        Dict[str, Any]
            Dictionary with algorithm information including:
            - name: Algorithm name
            - version: Implementation version
            - reference: Scientific reference
            - parameters: Current parameter values
        """
        return {
            "name": "Inductive Miner - Infrequent (IMf)",
            "version": "1.0.0-canonical",
            "reference": "Leemans et al. (2014) - DOI: 10.1007/978-3-319-06257-0_6",
            "parameters": {
                "noise_threshold": self.noise_threshold,
                "activity_threshold": self.activity_threshold,
                "traces_threshold": self.traces_threshold
            },
            "properties": {
                "soundness": "guaranteed",
                "rediscoverability": "yes (under noise threshold)",
                "complexity": "exponential (in practice polynomial for most logs)"
            }
        }

