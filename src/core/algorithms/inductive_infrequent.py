"""
Inductive Miner - Infrequent (IMf) - Paper-Based Implementation

This module implements the Inductive Miner - Infrequent algorithm as described in:

    Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P. (2014):
    Discovering Block-Structured Process Models from Event Logs Containing Infrequent Behaviour.
    Business Process Management Workshops. BPM 2013. Lecture Notes in Business Information Processing,
    vol 171. Springer, Cham. DOI: 10.1007/978-3-319-06257-0_6

Algorithm Overview 
--------------------------------
"In each recursion step, ﬁrst the operator and cut selection steps of IM are performed
by IMi. If that would result in the ﬂower model, the procedure is applied again, with
the infrequent behaviour ﬁlters in operator and cut selection, base cases and log
splitting, such that in all steps of IM ﬁlters are applied by IMi."

Key Filters Implemented:
------------------------
1. Base Case Filters (Section 3.2):
   - Single Activities: Only discover single 'a' if avg occurrences close to 1
   - Empty Traces: Only discover ×(τ,...) if ε is frequent enough

2. Operator/Cut Selection Filters (Section 3.1):
   - Filter infrequent edges from DFG before cut detection

3. Log Splitting Filters (Section 3.3):
   - × (XOR): Assign trace to partition explaining most activities
   - → (Sequence): Optimal split minimizing removed events
   - ∧ (Parallel): No filtering (any interleaving is valid)
   - ↺ (Loop): Add empty traces for invalid loop starts/ends
"""

from typing import Dict, Tuple, Optional, List, Set, Any, cast
from core.graphs.dfg import DFG
from core.graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from core.log_processing.splits import exclusive_split, parallel_split, sequence_split, loop_split
from core.log_processing.splits_imf import (
    exclusive_split_imf,
    sequence_split_imf,
    parallel_split_imf,
    loop_split_imf,
    is_single_activity_frequent,
    is_empty_trace_frequent
)
from utils.logger import get_logger
from core.algorithms.inductive import InductiveMining

logger = get_logger("InductiveMiningInfrequent")


class InductiveMiningInfrequent(InductiveMining):
    """
    Paper-based implementation of Inductive Miner - Infrequent (IMf).
    
    This implementation strictly follows the algorithm described in the 2014 paper
    by Leemans et al., implementing:
    
    1. Two-phase cut detection (full DFG, then filtered DFG)
    2. Base case filters for single activities and empty traces
    3. Log splitting filters for XOR, Sequence, and Loop operators
    4. Fall-through handling with infrequent activity filtering
    
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
        self.noise_threshold: float = 0.2  # Paper default
        self._last_noise_threshold: float = -1.0
        self._use_imf_filters: bool = False  # Track whether to use IMf filters
        logger.info("Initialized IMf (Inductive Miner - Infrequent) with paper-based algorithm")

    def generate_graph(
        self,
        activity_threshold: float = 0.0,
        traces_threshold: float = 0.0,
        noise_threshold: float = 0.2,
        **kwargs
    ):
        """
        Public entry point for process discovery using IMf.
        
        Parameters:
        -----------
        activity_threshold : float
            Minimum frequency threshold for activities (0.0 - 1.0)
        traces_threshold : float  
            Minimum frequency threshold for traces (0.0 - 1.0)
        noise_threshold : float
            Noise threshold for edge filtering (0.0 - 1.0)
            Recommended: 0.2 (20%)
        """
        # Validate noise threshold
        if not (0.0 <= noise_threshold <= 1.0):
            logger.warning(f"Invalid noise_threshold {noise_threshold}, clamping to [0.0, 1.0]")
            noise_threshold = max(0.0, min(1.0, noise_threshold))
        
        # Update threshold
        self.noise_threshold = noise_threshold
        
        logger.info(f"Starting IMf discovery with noise_threshold={noise_threshold}")
        logger.info(f"Pre-filtering: activity_threshold={activity_threshold}, "
                   f"traces_threshold={traces_threshold}")
        
        # Pre-filtering (activity and trace thresholds)
        events_to_remove = self.get_events_to_remove(activity_threshold)
        min_traces_frequency = self.calculate_minimum_traces_frequency(traces_threshold)
        
        from core.log_processing.filters import filter_traces, filter_events
        filtered_log = filter_traces(self.log, min_traces_frequency)
        filtered_log = filter_events(filtered_log, events_to_remove)
        
        # Check if regeneration needed
        log_changed = filtered_log != self.filtered_log
        threshold_changed = self._last_noise_threshold != noise_threshold
        
        if not log_changed and not threshold_changed:
            logger.debug("No changes detected - skipping regeneration")
            return
        
        # Update state
        self.activity_threshold = activity_threshold
        self.traces_threshold = traces_threshold
        self.filtered_log = filtered_log
        self._last_noise_threshold = noise_threshold
        
        # Generate process tree
        logger.info("Starting Inductive Mining Infrequent")
        from core.graphs.visualization.inductive_graph import InductiveGraph
        
        # Reset filter flag - start without filters
        self._use_imf_filters = False
        process_tree = self._inductive_mining_imf(self.filtered_log)
        
        self.graph = InductiveGraph(
            process_tree,
            frequency=self.appearance_frequency,
            node_sizes=self.node_sizes,
        )

    def inductive_mining(self, log: Dict[Tuple[str, ...], int]):
        """
        Override parent's inductive_mining to use IMf algorithm.
        
        This ensures that both direct calls and recursive calls use the
        paper-based IMf algorithm with proper filtering.
        """
        return self._inductive_mining_imf(log)

    def _inductive_mining_imf(self, log: Dict[Tuple[str, ...], int]):
        """
        Paper-based IMf algorithm with two-phase approach.
        
        Paper Algorithm (Section 3):
        ----------------------------
        "In each recursion step, ﬁrst the operator and cut selection steps of IM are 
        performed by IMi. If that would result in the ﬂower model, the procedure is 
        applied again, with the infrequent behaviour ﬁlters."
        
        Implementation:
        ---------------
        1. Try standard IM (no filters)
        2. If would result in flower model, retry with IMf filters:
           - Filter edges in DFG
           - Apply base case filters
           - Apply log splitting filters
        """
        if not log:
            return "tau"
        
        # === Phase 1: Try standard IM approach ===
        self._use_imf_filters = False
        
        # Check base cases (standard, no filter)
        if tree := self._base_cases_imf(log):
            return tree
        
        # Skip cut detection if empty trace present
        if tuple() not in log:
            # Try cuts on full DFG (standard IM)
            if result := self._try_cuts_standard(log):
                operator, sublogs = result
                logger.debug(f"Phase 1 SUCCESS: {operator} cut found")
                return (operator, *[self._inductive_mining_imf(sublog) for sublog in sublogs])
        
        # === Phase 2: Apply IMf filters ===
        logger.debug("Phase 1 failed - applying IMf filters")
        self._use_imf_filters = True
        
        # Handle empty trace with filter
        if tuple() in log:
            return self._handle_empty_trace_imf(log)
        
        # Try cuts on filtered DFG with filtered log splitting
        if self.noise_threshold > 0.0:
            if result := self._try_cuts_filtered(log):
                operator, sublogs = result
                logger.debug(f"Phase 2 SUCCESS: {operator} cut found with filtering")
                return (operator, *[self._inductive_mining_imf(sublog) for sublog in sublogs])
        
        # === Fall-through: Flower model ===
        return self._fallthrough_imf(log)

    def _base_cases_imf(self, log: Dict[Tuple[str, ...], int]) -> Optional[str]:
        """
        Check base cases with IMf filters (Section 3.2).
        
        Base Cases:
        -----------
        1. Empty log -> tau
        2. Single empty trace -> tau
        3. Single activity:
           - If avg occurrences ≈ 1 -> activity
           - If avg occurrences > threshold -> need loop (not base case)
        """
        if not log:
            return "tau"
        
        if len(log) == 1:
            trace = list(log.keys())[0]
            
            # Empty trace
            if len(trace) == 0:
                return "tau"
            
            # Single activity in single trace
            if len(trace) == 1:
                return trace[0]
        
        # Check for single-activity log (may have multiple traces)
        log_alphabet = self.get_log_alphabet(log)
        
        if len(log_alphabet) == 1:
            activity = list(log_alphabet)[0]
            
            # IMPORTANT: If empty traces exist, this is NOT a base case!
            # The empty traces need to be handled via XOR(tau, activity)
            # This is done in _handle_empty_trace_imf, not here
            if tuple() in log:
                return None  # Let the main algorithm handle empty traces
            
            # Apply IMf filter: check if single activity is appropriate
            if self._use_imf_filters:
                if is_single_activity_frequent(log, self.noise_threshold):
                    logger.debug(f"Base case (IMf filter): single activity '{activity}'")
                    return activity
                else:
                    # Average occurrences too high - need loop model
                    logger.debug(f"Base case (IMf filter): '{activity}' needs loop (avg > threshold)")
                    return None
            else:
                # Check if activity only occurs once per trace
                all_single = all(
                    trace.count(activity) == 1 
                    for trace in log.keys() 
                    if trace
                )
                if all_single:
                    return activity
        
        return None

    def _handle_empty_trace_imf(self, log: Dict[Tuple[str, ...], int]):
        """
        Handle empty trace with IMf filter (Section 3.2).
        
        Paper:
        ------
        "IMi only discovers x(tau, ...) if epsilon is frequent enough compared to the 
        number of traces in the log and with respect to k. If epsilon is not frequent 
        enough, IMi filters epsilon from L and recurses on L without epsilon."
        """
        if tuple() not in log:
            return None
        
        if self._use_imf_filters and self.noise_threshold > 0.0:
            if is_empty_trace_frequent(log, self.noise_threshold):
                # Empty trace is frequent - model with XOR(tau, ...)
                logger.debug("Empty trace is frequent - using XOR(tau, ...)")
                log_without_empty = {k: v for k, v in log.items() if k != tuple()}
                return ("xor", "tau", self._inductive_mining_imf(log_without_empty))
            else:
                # Empty trace is infrequent - filter it out
                logger.debug("Empty trace is infrequent - filtering and continuing")
                log_without_empty = {k: v for k, v in log.items() if k != tuple()}
                return self._inductive_mining_imf(log_without_empty)
        else:
            # Standard handling (no filter)
            log_without_empty = {k: v for k, v in log.items() if k != tuple()}
            return ("xor", "tau", self._inductive_mining_imf(log_without_empty))

    def _try_cuts_standard(
        self, 
        log: Dict[Tuple[str, ...], int]
    ) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Try cuts on full DFG with standard log splitting (Phase 1).
        """
        if not log:
            return None
        
        try:
            dfg = DFG(log)
            
            # Try cuts in paper order
            if partitions := exclusive_cut(dfg):
                if len(partitions) > 1:
                    sublogs = exclusive_split(log, cast(List[Set[str]], partitions))
                    if self._validate_split(sublogs):
                        return ("xor", sublogs)
            
            if partitions := sequence_cut(dfg):
                if len(partitions) > 1:
                    sublogs = sequence_split(log, cast(List[Set[str]], partitions))
                    if self._validate_split(sublogs):
                        return ("seq", sublogs)
            
            if partitions := parallel_cut(dfg):
                if len(partitions) > 1:
                    sublogs = parallel_split(log, cast(List[Set[str]], partitions))
                    if self._validate_split(sublogs):
                        return ("par", sublogs)
            
            if partitions := loop_cut(dfg):
                if len(partitions) > 1:
                    sublogs = loop_split(log, cast(List[Set[str]], partitions))
                    if self._validate_split(sublogs):
                        return ("loop", sublogs)
                        
        except Exception as e:
            logger.error(f"Error in standard cut detection: {e}")
        
        return None

    def _try_cuts_filtered(
        self, 
        log: Dict[Tuple[str, ...], int]
    ) -> Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]:
        """
        Try cuts on filtered DFG with IMf log splitting (Phase 2).
        
        Uses:
        - Filtered DFG (infrequent edges removed) for cut detection
        - IMf log splitting filters for creating sublogs
        """
        if not log:
            return None
        
        try:
            # Create filtered DFG
            filtered_dfg = self._create_filtered_dfg(log)
            
            if not filtered_dfg.get_nodes():
                logger.debug("Filtered DFG has no nodes")
                return None
            
            # Try cuts with IMf log splitting
            if partitions := exclusive_cut(filtered_dfg):
                if len(partitions) > 1:
                    # Use IMf filtered splitting
                    sublogs = exclusive_split_imf(
                        log, cast(List[Set[str]], partitions), self.noise_threshold
                    )
                    if self._validate_split(sublogs):
                        return ("xor", sublogs)
            
            if partitions := sequence_cut(filtered_dfg):
                if len(partitions) > 1:
                    # Use IMf filtered splitting (optimal split)
                    sublogs = sequence_split_imf(
                        log, cast(List[Set[str]], partitions), self.noise_threshold
                    )
                    if self._validate_split(sublogs):
                        return ("seq", sublogs)
            
            if partitions := parallel_cut(filtered_dfg):
                if len(partitions) > 1:
                    # Parallel: no filtering needed
                    sublogs = parallel_split_imf(
                        log, cast(List[Set[str]], partitions), self.noise_threshold
                    )
                    if self._validate_split(sublogs):
                        return ("par", sublogs)
            
            if partitions := loop_cut(filtered_dfg):
                if len(partitions) > 1:
                    # Use IMf filtered splitting (empty traces for invalid starts/ends)
                    sublogs = loop_split_imf(
                        log, cast(List[Set[str]], partitions), self.noise_threshold
                    )
                    if self._validate_split(sublogs):
                        return ("loop", sublogs)
                        
        except Exception as e:
            logger.error(f"Error in filtered cut detection: {e}")
        
        return None

    def _validate_split(
        self, 
        splits: List[Dict[Tuple[str, ...], int]]
    ) -> bool:
        """
        Validate that a log split is acceptable.
        
        Criteria:
        - At least 2 sublogs
        - At least one sublog must be non-trivial (not just empty traces)
        """
        if not splits or len(splits) < 2:
            return False
        
        non_trivial_count = 0
        for split in splits:
            if split:
                # Check if split has non-empty traces
                has_content = any(trace for trace in split.keys() if trace)
                if has_content:
                    non_trivial_count += 1
        
        return non_trivial_count >= 1

    def _fallthrough_imf(self, log: Dict[Tuple[str, ...], int]):
        """
        IMf-specific fallthrough (flower model with potential filtering).
        
        Paper:
        ------
        When no cut can be found even with filtering, create a flower model.
        For IMf, we may filter infrequent activities from the flower model.
        """
        log_alphabet = self.get_log_alphabet(log)

        # Handle empty trace
        if tuple() in log:
            if self._use_imf_filters:
                return self._handle_empty_trace_imf(log)
            else:
                log_without_empty = {k: v for k, v in log.items() if k != tuple()}
                return ("xor", "tau", self._inductive_mining_imf(log_without_empty))

        # Single activity with repetition -> loop
        if len(log_alphabet) == 1:
            activity = list(log_alphabet)[0]
            # Check if activity repeats in traces
            has_repetition = any(
                trace.count(activity) > 1 
                for trace in log.keys() 
                if trace
            )
            if has_repetition:
                return ("loop", activity, "tau")
            else:
                return activity

        # Filter infrequent activities from flower model if IMf filters enabled
        if self._use_imf_filters and self.noise_threshold > 0.0:
            # Compute activity frequencies
            activity_freq: Dict[str, int] = {}
            for trace, freq in log.items():
                for activity in trace:
                    activity_freq[activity] = activity_freq.get(activity, 0) + freq
            
            if activity_freq:
                max_freq = max(activity_freq.values())
                cutoff = max_freq * self.noise_threshold
                
                # Keep only frequent activities
                frequent_activities = {
                    act for act, freq in activity_freq.items() 
                    if freq >= cutoff
                }
                
                if frequent_activities and len(frequent_activities) < len(log_alphabet):
                    logger.debug(f"IMf fallthrough: filtering {len(log_alphabet) - len(frequent_activities)} "
                               f"infrequent activities from flower model")
                    log_alphabet = frequent_activities

        # Flower model
        if len(log_alphabet) == 1:
            return ("loop", list(log_alphabet)[0], "tau")
        
        return ("loop", "tau", *sorted(log_alphabet))

    def _create_filtered_dfg(self, log: Dict[Tuple[str, ...], int]) -> DFG:
        """
        Create filtered DFG by removing infrequent edges (Section 3.1).
        
        Edge filtering threshold:
            threshold = max_edge_frequency × noise_threshold
        
        Only edges with frequency >= threshold are kept.
        """
        if not log:
            return DFG()
        
        # Compute edge frequencies
        edge_freq = self._compute_edge_frequencies(log)
        
        if not edge_freq:
            return DFG()
        
        # Calculate threshold
        max_freq = max(edge_freq.values())
        threshold = max_freq * self.noise_threshold
        
        logger.debug(f"Edge filtering: max={max_freq}, threshold={threshold:.2f}")
        
        # Identify frequent edges and connected nodes
        frequent_edges = []
        connected_nodes: Set[str] = set()
        
        for (src, tgt), freq in edge_freq.items():
            if freq >= threshold:
                frequent_edges.append((src, tgt))
                connected_nodes.add(src)
                connected_nodes.add(tgt)
        
        # Create filtered DFG
        filtered_dfg = DFG()
        
        # Add connected nodes
        for node in connected_nodes:
            filtered_dfg.add_node(node)
        
        # Add frequent edges
        for src, tgt in frequent_edges:
            filtered_dfg.add_edge(src, tgt)
        
        # Preserve start/end information
        self._preserve_start_end_nodes(filtered_dfg, log)
        
        logger.debug(f"Filtered DFG: {len(connected_nodes)} nodes, {len(frequent_edges)} edges "
                    f"(filtered {len(edge_freq) - len(frequent_edges)} edges)")
        
        return filtered_dfg

    def _compute_edge_frequencies(
        self, 
        log: Dict[Tuple[str, ...], int]
    ) -> Dict[Tuple[str, str], int]:
        """
        Compute frequency of each directly-follows relation.
        """
        edge_freq: Dict[Tuple[str, str], int] = {}
        
        for trace, freq in log.items():
            if len(trace) < 2:
                continue
            
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                edge_freq[edge] = edge_freq.get(edge, 0) + freq
        
        return edge_freq

    def _preserve_start_end_nodes(
        self, 
        dfg: DFG, 
        log: Dict[Tuple[str, ...], int]
    ):
        """
        Preserve start and end node information in filtered DFG.
        """
        try:
            if hasattr(dfg, 'start_nodes') and hasattr(dfg, 'end_nodes'):
                start_nodes = {
                    trace[0] for trace in log.keys() if trace
                }
                end_nodes = {
                    trace[-1] for trace in log.keys() if trace
                }
                
                # Only include nodes that are in the DFG
                dfg_nodes = set(dfg.get_nodes())
                dfg.start_nodes = start_nodes & dfg_nodes  # type: ignore
                dfg.end_nodes = end_nodes & dfg_nodes  # type: ignore
                
        except Exception as e:
            logger.debug(f"Could not preserve start/end nodes: {e}")

    # =========================================================================
    # Public API
    # =========================================================================

    def get_noise_threshold(self) -> float:
        """Get current noise threshold."""
        return self.noise_threshold
    
    # Backward compatibility methods
    def calculate_cut(self, log: Dict[Tuple[str, ...], int]) -> Optional[tuple]:
        """
        Backward compatibility: Call appropriate cut detection based on IMf state.
        This method is kept for backward compatibility with existing code.
        
        Returns:
        --------
        Optional[Tuple[str, List[Dict[Tuple[str, ...], int]]]]
            (operator, sublogs_list) or None
        """
        # Try Phase 1 (standard)
        if result := self._try_cuts_standard(log):
            operator, sublogs = result
            return (operator, sublogs)
        
        # Try Phase 2 (filtered) if noise_threshold > 0
        if self.noise_threshold > 0.0:
            if result := self._try_cuts_filtered(log):
                operator, sublogs = result
                return (operator, sublogs)
        
        return None
    
    def calculate_cut(self, log: Dict[Tuple[str, ...], int]) -> Optional[tuple]:
        """Alias for calculate_cut (correct spelling)."""
        return self.calculate_cut(log)
        
    def set_noise_threshold(self, threshold: float):
        """Set noise threshold (0.0 - 1.0)."""
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"Noise threshold must be between 0.0 and 1.0, got {threshold}")
        self.noise_threshold = threshold

    def get_algorithm_info(self) -> Dict[str, Any]:
        """Get information about the algorithm configuration."""
        return {
            "name": "Inductive Miner - Infrequent (IMf)",
            "version": "2.0.0-paper-based",
            "reference": "Leemans et al. (2014) - DOI: 10.1007/978-3-319-06257-0_6",
            "parameters": {
                "noise_threshold": self.noise_threshold,
                "activity_threshold": self.activity_threshold,
                "traces_threshold": self.traces_threshold
            },
            "features": {
                "base_case_filters": True,
                "log_splitting_filters": True,
                "two_phase_cut_detection": True
            },
            "properties": {
                "soundness": "guaranteed",
                "rediscoverability": "yes (under noise threshold)"
            }
        }

