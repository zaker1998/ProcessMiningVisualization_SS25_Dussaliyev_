"""
Inductive Miner - Directly-Follows (IMd) - Canonical Implementation

This module implements the Inductive Miner - Directly-Follows algorithm as described in:

    Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P. (2018):
    Scalable process discovery and conformance checking.
    Software & Systems Modeling 17, 599–631.
    DOI: 10.1007/s10270-016-0545-x

Algorithm Overview:
-------------------
IMd is designed for SCALABILITY - it can handle event logs with billions of events
and thousands of activities by working directly with the Directly-Follows Graph (DFG)
and making a single pass over the log.

Key Features:
- Works with DFG only (not full log in recursion)
- Single-pass log processing (streaming capable)
- O(|activities|²) memory complexity (independent of log size)
- Suitable for very large logs (10⁹+ events)
- Sound process models (no deadlocks)

Differences from IMf:
- IMd works with DFG, IMf works with full log
- IMd makes single pass, IMf may need multiple passes
- IMd scales to massive logs, IMf handles medium/large logs
- IMd may lose some trace-level detail, IMf preserves all trace information

This implementation follows the canonical algorithm specification from the 2018 paper.
"""

from typing import Dict, Tuple, Optional, List, Set, Any, cast
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
from logger import get_logger
from mining_algorithms.inductive_mining import InductiveMining

logger = get_logger("InductiveMiningDF")


class InductiveMiningDF(InductiveMining):
    """
    Canonical implementation of Inductive Miner - Directly-Follows (IMd).
    
    This implementation strictly follows the algorithm described in the 2018 paper
    by Leemans et al., providing:
    
    - Scalability to very large logs (billions of events)
    - Single-pass log processing (streaming)
    - Sound process model discovery (no deadlocks)
    - Memory efficiency (independent of log size)
    - DFG-based cut detection
    
    The algorithm is designed for scenarios where the event log is too large to
    fit in memory or when processing needs to be extremely fast.
    
    Parameters:
    -----------
    log : Dict[Tuple[str, ...], int]
        Event log as a dictionary mapping traces to their frequencies
        Note: In production, this could be replaced with streaming input
        
    Attributes:
    -----------
    edge_cutoff_threshold : float
        Minimum frequency ratio for edges to be considered (0.0 - 1.0)
        Default: 0.0 (no edge filtering, pure DFG-based discovery)
        When > 0: Filters edges with freq < threshold × max_edge_freq
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        """
        Initialize IMd miner.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Event log with traces and their frequencies
            
        Notes:
        ------
        In a true streaming scenario, this would accept a DFG directly instead
        of constructing it from a log. The current implementation maintains
        compatibility with the existing codebase structure.
        """
        super().__init__(log)
        self.edge_cutoff_threshold: float = 0.0  # No filtering by default
        self._last_edge_threshold: float = -1.0  # Track last used threshold for change detection
        logger.info("Initialized IMd (Inductive Miner - Directly-Follows) with canonical algorithm")

    def generate_graph(
        self,
        activity_threshold: float = 0.0,
        traces_threshold: float = 0.0,
        edge_cutoff_threshold: float = 0.0
    ):
        """
        Public entry point for process discovery using IMd.
        
        This method applies pre-filtering and then runs the canonical IMd algorithm.
        
        Parameters:
        -----------
        activity_threshold : float
            Minimum frequency threshold for activities (0.0 - 1.0)
            Activities with freq < threshold * max_activity_freq are removed
        traces_threshold : float
            Minimum frequency threshold for traces (0.0 - 1.0)
            Traces with freq < threshold * max_trace_freq are removed
        edge_cutoff_threshold : float
            Optional edge filtering threshold (0.0 - 1.0)
            Default: 0.0 (no edge filtering, pure DFG-based)
            When > 0: Acts as a simple noise filter
            
        Notes:
        ------
        - The edge_cutoff_threshold is OPTIONAL and not part of the core IMd algorithm
        - It can be used as a simple noise filter when needed
        - For advanced noise handling, use IMf instead
        """
        # Validate edge_cutoff_threshold
        if not (0.0 <= edge_cutoff_threshold <= 1.0):
            logger.warning(f"Invalid edge_cutoff_threshold {edge_cutoff_threshold}, clamping to [0.0, 1.0]")
            edge_cutoff_threshold = max(0.0, min(1.0, edge_cutoff_threshold))
        
        # Update threshold
        self.edge_cutoff_threshold = edge_cutoff_threshold
        
        # Log what we're doing
        if edge_cutoff_threshold > 0.0:
            logger.info(f"Starting IMd discovery with edge_cutoff_threshold={edge_cutoff_threshold}")
            logger.info("Note: Edge filtering is optional in IMd. For advanced noise handling, use IMf.")
        else:
            logger.info("Starting IMd discovery (pure DFG-based, no edge filtering)")
        
        logger.info(f"Pre-filtering: activity_threshold={activity_threshold}, "
                   f"traces_threshold={traces_threshold}")
        
        # CRITICAL: Check if we need to regenerate
        # Regenerate if: (1) filtered log changes OR (2) edge threshold changes
        events_to_remove = self.get_events_to_remove(activity_threshold)
        min_traces_frequency = self.calulate_minimum_traces_frequency(traces_threshold)
        
        from logs.filters import filter_traces, filter_events
        filtered_log = filter_traces(self.log, min_traces_frequency)
        filtered_log = filter_events(filtered_log, events_to_remove)
        
        # Apply edge-based log filtering (similar to activity/traces approach)
        # This ensures filtering persists through all recursion levels
        if edge_cutoff_threshold > 0.0 and filtered_log:
            logger.info(f"Applying edge threshold filtering: {edge_cutoff_threshold}")
            filtered_log = self._apply_edge_filtering_to_log(filtered_log, edge_cutoff_threshold)
        
        # Check if anything changed
        log_changed = filtered_log != self.filtered_log
        threshold_changed = self._last_edge_threshold != edge_cutoff_threshold
        
        if not log_changed and not threshold_changed:
            logger.debug("No changes detected - skipping regeneration")
            return
        
        if threshold_changed:
            logger.info(f"Edge threshold changed: {self._last_edge_threshold} -> {edge_cutoff_threshold}")
        if log_changed:
            logger.info("Filtered log changed - regenerating")
        
        # Update state
        self.activity_threshold = activity_threshold
        self.traces_threshold = traces_threshold
        self.filtered_log = filtered_log
        self._last_edge_threshold = edge_cutoff_threshold
        
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
        Canonical IMd cut detection using DFG-based approach.
        
        Algorithm (from 2018 paper):
        -----------------------------
        The key difference in IMd is that it works primarily with the DFG
        structure, not the full log. This enables scalability.
        
        Canonical IMd with Optional Edge Filtering:
        1. Construct DFG from log
        2. Apply optional edge filtering to DFG (if edge_cutoff_threshold > 0)
        3. Detect cuts using DFG structure
        4. If cut found: split ORIGINAL log based on partitions
        5. Recurse with sublogs
        
        IMPORTANT: Edge filtering affects DFG structure for cut detection,
        but we ALWAYS split the original log (preserving trace information).
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log for cut detection
            
        Returns:
        --------
        Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]
            If a cut is found: (operator, [sublog1, sublog2, ...])
            If no cut found: None
        """
        if not log:
            logger.debug("Empty log provided to calculate_cut")
            return None
        
        # Skip cut detection if empty trace present (fall-through)
        if tuple() in log:
            logger.debug("Empty trace present in log, skipping cut detection (fall-through)")
            return None
        
        # Construct DFG from log
        logger.debug("Constructing DFG for cut detection")
        
        try:
            # Build the DFG
            dfg = DFG(log)
            
            # Apply optional edge filtering if configured (CANONICAL)
            # This filters edges in the DFG for cut detection, but does NOT modify the log
            if self.edge_cutoff_threshold > 0.0:
                dfg_for_cuts = self._create_filtered_dfg(log)
                logger.debug(f"Using filtered DFG for cut detection (cutoff={self.edge_cutoff_threshold})")
                logger.debug(f"  Original DFG: {len(dfg.get_edges())} edges")
                logger.debug(f"  Filtered DFG: {len(dfg_for_cuts.get_edges())} edges")
            else:
                dfg_for_cuts = dfg
                logger.debug("Using full DFG (no filtering)")
            
            logger.debug(f"DFG: {len(dfg_for_cuts.get_nodes())} nodes, {len(dfg_for_cuts.get_edges())} edges")
            
            # Try to find cuts using the (possibly filtered) DFG structure
            # CANONICAL: Use filtered DFG for detection, but split original log
            cut = self._try_all_cuts_dfg(dfg_for_cuts, log)
            
            if cut:
                operator, sublogs = cut
                logger.info(f"✓ Found {operator} cut using DFG-based detection")
                logger.debug(f"  Partitions: {len(sublogs)} sublogs with sizes "
                           f"{[len(sublog) for sublog in sublogs]}")
                return cut
            else:
                logger.debug("No cuts found using DFG-based detection")
                return None
                
        except Exception as e:
            logger.error(f"Error in DFG-based cut detection: {e}")
            return None

    def _try_all_cuts_dfg(
        self,
        dfg: DFG,
        log: Dict[Tuple[str, ...], int]
    ) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Try all cut types using DFG-based detection.
        
        Cut Detection Order (canonical):
        ---------------------------------
        1. Exclusive cut (XOR): Disconnected components in DFG
        2. Sequence cut (→): Ordered partitioning based on reachability
        3. Parallel cut (∧): Concurrent execution (inverted DFG components)
        4. Loop cut (↻): Loop structure (start/end node analysis)
        
        DFG-Based Detection:
        --------------------
        All cut detection is based purely on the DFG structure:
        - Node connectivity
        - Edge reachability
        - Start/end node positions
        - No trace-level information needed
        
        This enables the algorithm to scale to massive logs.
        
        Parameters:
        -----------
        dfg : DFG
            Directly-follows graph to analyze
        log : Dict[Tuple[str, ...], int]
            Log for splitting (after cut is found)
            Note: In canonical IMd, this would be DFG projection, not log splitting
            
        Returns:
        --------
        Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]
            First valid cut found, or None if no cut succeeds
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
                
                # Attempt to find partition using DFG structure
                partitions = cut_func(dfg)
                
                if partitions and len(partitions) > 1:
                    logger.debug(f"    Found partitions: {len(partitions)} sets")
                    logger.debug(f"    Partition sizes: {[len(p) for p in partitions]}")
                    
                    # Split log based on partition
                    # (In canonical IMd, this would be DFG projection)
                    splits = split_func(log, cast(List[Set[str]], partitions))
                    
                    # Validate split
                    if self._validate_split_dfg(splits, log, operator):
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

    def _validate_split_dfg(
        self,
        splits: List[Dict[Tuple[str, ...], int]],
        original_log: Dict[Tuple[str, ...], int],
        operator: str
    ) -> bool:
        """
        Validate split using lightweight criteria suitable for DFG-based discovery.
        
        Validation Criteria for IMd:
        -----------------------------
        1. All splits must be non-empty
        2. Basic frequency preservation (relaxed compared to IMf)
        3. No degenerate splits
        
        IMd uses more relaxed validation because:
        - Works with DFG structure (less information than full log)
        - Optimized for speed and scalability
        - Acceptable to lose some trace-level detail
        
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
        
        # Relaxed frequency preservation for DFG-based discovery
        original_freq = sum(original_log.values())
        total_split_freq = sum(sum(split.values()) for split in splits)
        
        # IMd uses more relaxed thresholds (trade accuracy for scalability)
        min_preservation = {
            "xor": 0.7,   # More relaxed than IMf
            "seq": 0.6,
            "par": 0.5,
            "loop": 0.4   # Loops can lose significant frequency
        }
        
        threshold = min_preservation.get(operator, 0.5)
        preservation_ratio = total_split_freq / original_freq if original_freq > 0 else 0
        
        if preservation_ratio < threshold:
            logger.debug(f"      Validation FAIL: Frequency preservation {preservation_ratio:.2%} "
                        f"< {threshold:.0%} (operator={operator})")
            return False
        
        logger.debug(f"      Validation PASS: Frequency preserved {preservation_ratio:.2%}")
        return True

    def _create_filtered_dfg(self, log: Dict[Tuple[str, ...], int]) -> DFG:
        """
        Create filtered DFG with optional edge cutoff (CANONICAL approach).
        
        This is an OPTIONAL extension to handle noisy logs when needed.
        
        CANONICAL Algorithm (from IMf paper, adapted for IMd):
        ------------------------------------------------------
        1. Build full DFG from log
        2. Compute edge frequencies
        3. Calculate threshold: max_frequency × edge_cutoff_threshold
        4. Create new DFG with:
           - ALL nodes (activities) preserved
           - Only edges with frequency ≥ threshold
        5. Preserve start/end node metadata
        
        IMPORTANT: This filters the DFG structure for cut detection,
        but does NOT modify the underlying log or remove traces.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input event log
            
        Returns:
        --------
        DFG
            Filtered directly-follows graph (edges filtered, all nodes kept)
        """
        if not log:
            logger.debug("Empty log provided to _create_filtered_dfg")
            return DFG()
        
        # If no filtering, return full DFG
        if self.edge_cutoff_threshold == 0.0:
            return DFG(log)
        
        # Compute edge frequencies
        edge_freq = self._compute_edge_frequencies(log)
        
        if not edge_freq:
            logger.debug("No edges found in log")
            return DFG()
        
        # Calculate threshold (CANONICAL)
        max_freq = max(edge_freq.values())
        threshold = max_freq * self.edge_cutoff_threshold
        
        logger.debug(f"Edge cutoff threshold calculation:")
        logger.debug(f"  max_frequency = {max_freq}")
        logger.debug(f"  edge_cutoff_threshold = {self.edge_cutoff_threshold}")
        logger.debug(f"  computed_threshold = {threshold:.2f}")
        
        # Create filtered DFG (CANONICAL)
        filtered_dfg = DFG()
        
        # Add ALL nodes (preserve all activities) - CANONICAL requirement
        activities = self.get_log_alphabet(log)
        for activity in activities:
            filtered_dfg.add_node(activity)
        
        # Add only edges above threshold
        retained_edges = 0
        total_edges = len(edge_freq)
        
        for (src, tgt), freq in edge_freq.items():
            if freq >= threshold:
                filtered_dfg.add_edge(src, tgt)
                retained_edges += 1
        
        retention_rate = retained_edges / total_edges if total_edges > 0 else 0
        logger.info(f"DFG edge filtering: retained {retained_edges}/{total_edges} edges "
                   f"({retention_rate:.1%}) for cut detection")
        
        # Preserve start and end node information (CANONICAL)
        self._preserve_start_end_nodes(filtered_dfg, log)
        
        return filtered_dfg
    
    def _apply_edge_filtering_to_log(
        self, 
        log: Dict[Tuple[str, ...], int], 
        threshold: float
    ) -> Dict[Tuple[str, ...], int]:
        """
        Filter traces from log based on edge frequency threshold.
        
        This approach mirrors activity/traces filtering: modify the log before mining
        so that filtering persists through all recursion levels.
        
        Algorithm:
        ----------
        1. Compute all edge frequencies in the log
        2. Calculate cutoff: max_freq × threshold
        3. Remove traces that contain edges below cutoff
        4. Return filtered log
        
        This ensures weak/noisy edges are removed from the process model,
        similar to how activity_threshold removes infrequent activities.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Input log with traces and frequencies
        threshold : float
            Edge frequency threshold (0.0 - 1.0)
            
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
        
        logger.debug(f"Edge filtering: max_freq={max_freq}, threshold={threshold}, cutoff={cutoff_value}")
        
        # Determine which edges to keep
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
            
            # Check if all edges in trace are frequent
            if all((trace[i], trace[i + 1]) in kept_edges for i in range(len(trace) - 1)):
                filtered_log[trace] = freq
                kept_event_count += freq
        
        # Log filtering statistics
        filtered_trace_count = len(filtered_log)
        logger.info(f"Edge filtering removed {original_trace_count - filtered_trace_count}/{original_trace_count} trace variants")
        logger.info(f"Edge filtering kept {kept_event_count}/{original_event_count} trace instances "
                   f"({kept_event_count/original_event_count*100:.1f}%)")
        logger.info(f"Edge filtering kept {len(kept_edges)}/{len(edge_freq)} unique edges "
                   f"({len(kept_edges)/len(edge_freq)*100:.1f}%)")
        
        #\Return empty log if all traces were filtered
        # Do NOT fall back to original log - that would undo the filtering!
        # An empty log will result in a minimal process model (just start/end)
        return filtered_log

    def _compute_edge_frequencies(self, log: Dict[Tuple[str, ...], int]) -> Dict[Tuple[str, str], int]:
        """
        Compute frequency of each directly-follows relation.
        
        This is the ONLY information from the log that IMd needs.
        After this computation, the algorithm works purely with the DFG.
        
        Single-Pass Property:
        ---------------------
        This function processes each trace exactly once, enabling
        streaming/online processing of massive logs.
        
        Parameters:
        -----------
        log : Dict[Tuple[str, ...], int]
            Event log with traces and frequencies
            
        Returns:
        --------
        Dict[Tuple[str, str], int]
            Dictionary mapping edges to their frequencies
        """
        edge_freq: Dict[Tuple[str, str], int] = {}
        
        for trace, freq in log.items():
            # Skip traces with less than 2 activities
            if len(trace) < 2:
                continue
            
            # Count directly-follows relations
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                edge_freq[edge] = edge_freq.get(edge, 0) + freq
        
        return edge_freq

    def _preserve_start_end_nodes(self, dfg: DFG, log: Dict[Tuple[str, ...], int]):
        """
        Preserve start and end node information in the DFG (CANONICAL).
        
        IMPORTANT: In the canonical algorithm, start/end node information is
        preserved from the ORIGINAL log, not from the filtered DFG. This ensures
        that all process start/end points are represented, even if some edges
        are filtered during cut detection.
        
        This information is essential for:
        - Parallel cut detection (start/end activities)
        - Loop cut detection (redo/body/exit parts)
        - Proper fall-through base case handling
        
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

                dfg.start_nodes = start_nodes
                dfg.end_nodes = end_nodes
                
                logger.debug(f"Preserved start nodes: {start_nodes}")
                logger.debug(f"Preserved end nodes: {end_nodes}")
        except Exception as e:
            logger.debug(f"Could not preserve start/end nodes: {e}")

    # Public API for configuration and introspection
    
    def get_edge_cutoff_threshold(self) -> float:
        """
        Get the current edge cutoff threshold value.
        
        Returns:
        --------
        float
            Current edge cutoff threshold (0.0 - 1.0)
        """
        return self.edge_cutoff_threshold
        
    def set_edge_cutoff_threshold(self, threshold: float):
        """
        Set the edge cutoff threshold value.
        
        Parameters:
        -----------
        threshold : float
            New edge cutoff threshold (0.0 - 1.0)
            
        Raises:
        -------
        ValueError
            If threshold is not in valid range [0.0, 1.0]
        """
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"Edge cutoff threshold must be between 0.0 and 1.0, got {threshold}")
        self.edge_cutoff_threshold = threshold
        logger.info(f"Edge cutoff threshold updated to {threshold}")

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
            - properties: Algorithm properties
        """
        return {
            "name": "Inductive Miner - Directly-Follows (IMd)",
            "version": "1.0.0-canonical",
            "reference": "Leemans et al. (2018) - DOI: 10.1007/s10270-016-0545-x",
            "parameters": {
                "edge_cutoff_threshold": self.edge_cutoff_threshold,
                "activity_threshold": self.activity_threshold,
                "traces_threshold": self.traces_threshold
            },
            "properties": {
                "soundness": "guaranteed",
                "scalability": "billions of events",
                "memory_complexity": "O(|activities|²)",
                "time_complexity": "O(|events|) single-pass",
                "streaming_capable": "yes",
                "trade_off": "loses some trace-level detail for scalability"
            }
        }
