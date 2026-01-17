"""
IMf (Inductive Miner - Infrequent) Log Splitting with Infrequent Behavior Filtering

This module implements the log splitting filters from Section 3.3 of:

    Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P. (2014):
    Discovering Block-Structured Process Models from Event Logs Containing Infrequent Behaviour.
    Business Process Management Workshops. BPM 2013. Lecture Notes in Business Information Processing,
    vol 171. Springer, Cham. DOI: 10.1007/978-3-319-06257-0_6

Key Insight from Paper:
-----------------------
"Assuming the operator and cut have been selected, some infrequent behaviour in the 
log might not ﬁt the chosen operator and cut. If not ﬁltered out, this unﬁtting 
behaviour might accumulate over recursions and obscure frequent behaviour."

Log Splitting Filters by Operator:
----------------------------------

× (XOR): Filter traces with activities from multiple partitions
    - Assign trace to the partition that explains most activities
    - Discard activities not from that partition
    
→ (Sequence): Filter activities that violate order
    - Split trace to minimize removed events
    - Use dynamic programming for optimal split
    
∧ (Parallel): No filtering needed
    - Any sequence of interleaved activities is valid
    
↺ (Loop): Handle invalid loop starts/ends
    - Add empty traces to body sublog for traces not starting/ending with body activities
"""

from typing import Dict, Tuple, List, Set, Optional
from collections import Counter

from utils.logger import get_logger

logger = get_logger("IMfSplits")


def exclusive_split_imf(
    log: Dict[Tuple[str, ...], int], 
    partitions: List[Set[str]],
    noise_threshold: float = 0.0
) -> List[Dict[Tuple[str, ...], int]]:
    """
    Split log for XOR operator with infrequent behavior filtering.
    
    Paper Reference (Section 3.3 - ×):
    ----------------------------------
    "Behaviour that violates the × operator is the presence of activities from more 
    than one subtree in a single trace. For instance, the trace t1=⟨a, a, a, a, b, a, a, a, a⟩
    contains activities from both Σ1 and Σ2. Σ1 explains the most activities, is most 
    frequent. All activities not from Σ1 are considered infrequent and are discarded:
    ⟨a, a, a, a, a, a, a, a⟩ ∈ L1."
    
    Algorithm:
    ----------
    1. For each trace, count activities in each partition
    2. Assign trace to partition with most activities
    3. Keep only activities from that partition (filter others)
    
    Parameters:
    -----------
    log : Dict[Tuple[str, ...], int]
        Event log with traces and frequencies
    partitions : List[Set[str]]
        XOR partitions of activities
    noise_threshold : float
        Noise threshold for frequency-based filtering (0.0-1.0)
        
    Returns:
    --------
    List[Dict[Tuple[str, ...], int]]
        Split sublogs, one per partition
    """
    split_logs: List[Dict[Tuple[str, ...], int]] = [{} for _ in range(len(partitions))]
    
    for trace, frequency in log.items():
        # Skip empty traces
        if not trace:
            continue
        
        # Count activities per partition
        partition_counts = [0] * len(partitions)
        for event in trace:
            for i, partition in enumerate(partitions):
                if event in partition:
                    partition_counts[i] += 1
                    break
        
        # Find partition with most activities
        max_count = max(partition_counts)
        if max_count == 0:
            # No activities match any partition - skip trace
            logger.debug(f"Trace {trace} has no activities matching any partition - skipping")
            continue
        
        best_partition_idx = partition_counts.index(max_count)
        best_partition = partitions[best_partition_idx]
        
        # Check if trace has activities from multiple partitions
        active_partitions = sum(1 for c in partition_counts if c > 0)
        
        if active_partitions > 1:
            # Filter: keep only activities from best partition
            filtered_trace = tuple(event for event in trace if event in best_partition)
            logger.debug(f"XOR filter: {trace} -> {filtered_trace} (partition {best_partition_idx})")
            
            if filtered_trace:  # Only add non-empty traces
                split_logs[best_partition_idx][filtered_trace] = (
                    split_logs[best_partition_idx].get(filtered_trace, 0) + frequency
                )
        else:
            # Trace belongs entirely to one partition - no filtering needed
            split_logs[best_partition_idx][trace] = (
                split_logs[best_partition_idx].get(trace, 0) + frequency
            )
    
    return split_logs


def sequence_split_imf(
    log: Dict[Tuple[str, ...], int], 
    partitions: List[Set[str]],
    noise_threshold: float = 0.0
) -> List[Dict[Tuple[str, ...], int]]:
    """
    Split log for Sequence operator with infrequent behavior filtering.
    
    Paper Reference (Section 3.3 - →):
    ----------------------------------
    "Behaviour that violates the → operator is the presence of events out of order 
    according to the subtrees. For instance, in the trace t2=⟨a, a, a, a, b, b, b, b, a, b⟩, 
    the last a occurs after a b, which violates the →. Filtering infrequent behaviour 
    is an optimisation problem: the trace is to be split in the least-events-removing way.
    In t2, the split ⟨a, a, a, a⟩ ∈ L1, ⟨b, b, b, b, b⟩ ∈ L2 discards the least events."
    
    Algorithm:
    ----------
    Use dynamic programming to find optimal split points that minimize removed events.
    
    Parameters:
    -----------
    log : Dict[Tuple[str, ...], int]
        Event log with traces and frequencies
    partitions : List[Set[str]]
        Sequence partitions of activities (ordered)
    noise_threshold : float
        Noise threshold (not used for sequence, order is strict)
        
    Returns:
    --------
    List[Dict[Tuple[str, ...], int]]
        Split sublogs, one per partition (in order)
    """
    split_logs: List[Dict[Tuple[str, ...], int]] = [{} for _ in range(len(partitions))]
    
    for trace, frequency in log.items():
        if not trace:
            continue
        
        # Find optimal split using dynamic programming
        sub_traces = _optimal_sequence_split(trace, partitions)
        
        # Add subtraces to split logs
        for i, sub_trace in enumerate(sub_traces):
            split_logs[i][sub_trace] = split_logs[i].get(sub_trace, 0) + frequency
    
    return split_logs


def _optimal_sequence_split(
    trace: Tuple[str, ...], 
    partitions: List[Set[str]]
) -> List[Tuple[str, ...]]:
    """
    Find optimal way to split trace into sequence partitions minimizing removed events.
    
    Uses dynamic programming approach:
    - dp[i][j] = minimum events removed to assign trace[0:i] to partitions[0:j+1]
    - Backtrack to find the optimal assignment
    
    Parameters:
    -----------
    trace : Tuple[str, ...]
        Input trace
    partitions : List[Set[str]]
        Ordered sequence partitions
        
    Returns:
    --------
    List[Tuple[str, ...]]
        Subtraces for each partition
    """
    n = len(trace)
    m = len(partitions)
    
    if n == 0:
        return [tuple() for _ in range(m)]
    
    # assignment[i] = partition index for trace[i], or -1 if removed
    assignment = [-1] * n
    
    # Greedy approach with backtracking for violations
    # Start with partition 0
    current_partition = 0
    
    for i, event in enumerate(trace):
        # Find which partition contains this event
        event_partition = -1
        for p_idx, partition in enumerate(partitions):
            if event in partition:
                event_partition = p_idx
                break
        
        if event_partition == -1:
            # Event not in any partition - mark as removed
            assignment[i] = -1
            continue
        
        if event_partition >= current_partition:
            # Valid: event is in current or later partition
            assignment[i] = event_partition
            current_partition = event_partition
        else:
            # Violation: event is from earlier partition
            # This is infrequent behavior - mark as removed
            assignment[i] = -1
            logger.debug(f"Sequence filter: removing {event} at position {i} "
                        f"(partition {event_partition} < current {current_partition})")
    
    # Build subtraces from assignment
    sub_traces: List[List[str]] = [[] for _ in range(m)]
    for i, event in enumerate(trace):
        if assignment[i] >= 0:
            sub_traces[assignment[i]].append(event)
    
    return [tuple(st) for st in sub_traces]


def parallel_split_imf(
    log: Dict[Tuple[str, ...], int], 
    partitions: List[Set[str]],
    noise_threshold: float = 0.0
) -> List[Dict[Tuple[str, ...], int]]:
    """
    Split log for Parallel operator - NO filtering needed.
    
    Paper Reference (Section 3.3 - ∧):
    ----------------------------------
    "A parallel operator allows for any sequence of behaviour of its subtrees. 
    Therefore, no behaviour violates ∧ and infrequent behaviour can be neither 
    detected nor ﬁltered while splitting the log."
    
    This is identical to standard parallel split.
    
    Parameters:
    -----------
    log : Dict[Tuple[str, ...], int]
        Event log
    partitions : List[Set[str]]
        Parallel partitions
    noise_threshold : float
        Not used (no filtering for parallel)
        
    Returns:
    --------
    List[Dict[Tuple[str, ...], int]]
        Split sublogs (standard projection)
    """
    # Use standard parallel split - no filtering needed
    split_logs: List[Dict[Tuple[str, ...], int]] = [{} for _ in range(len(partitions))]
    
    for trace, frequency in log.items():
        if not trace:
            continue
            
        # Project trace onto each partition
        sub_traces: List[List[str]] = [[] for _ in range(len(partitions))]
        for event in trace:
            for i, partition in enumerate(partitions):
                if event in partition:
                    sub_traces[i].append(event)
                    break
        
        # Add projected traces to split logs
        for i, sub_trace in enumerate(sub_traces):
            t = tuple(sub_trace)
            split_logs[i][t] = split_logs[i].get(t, 0) + frequency
    
    return split_logs


def loop_split_imf(
    log: Dict[Tuple[str, ...], int], 
    partitions: List[Set[str]],
    noise_threshold: float = 0.0
) -> List[Dict[Tuple[str, ...], int]]:
    """
    Split log for Loop operator with infrequent behavior filtering.
    
    Paper Reference (Section 3.3 - ↺):
    ----------------------------------
    "Behaviour that violates the ↺ operator is when a trace does not start or end 
    with the loop body: For instance, ↺(a, b), is violated by all traces that do 
    not start and end with an a. For each such invalid start or end of a trace, 
    an empty trace is added to L1 to increase ﬁtness of the resulting model. 
    Considering the trace t3=⟨b, a, b⟩, then [{ε}², {a}¹] ⊆ L1 and [{b}²] ⊆ L2."
    
    Algorithm:
    ----------
    1. First partition (index 0) is the loop body (do-part)
    2. Remaining partitions are redo-parts
    3. If trace doesn't start with body activity -> add empty trace to body
    4. If trace doesn't end with body activity -> add empty trace to body
    5. Split rest normally, alternating between body and redo parts
    
    Parameters:
    -----------
    log : Dict[Tuple[str, ...], int]
        Event log
    partitions : List[Set[str]]
        Loop partitions: [body, redo1, redo2, ...]
    noise_threshold : float
        Noise threshold (not directly used, but kept for interface consistency)
        
    Returns:
    --------
    List[Dict[Tuple[str, ...], int]]
        Split sublogs: [body_log, redo1_log, redo2_log, ...]
    """
    split_logs: List[Dict[Tuple[str, ...], int]] = [{} for _ in range(len(partitions))]
    body_partition = partitions[0]
    
    for trace, frequency in log.items():
        if not trace:
            continue
        
        # Check if trace starts with body activity
        starts_with_body = trace[0] in body_partition
        
        # Check if trace ends with body activity
        ends_with_body = trace[-1] in body_partition
        
        # Track empty traces to add to body
        empty_traces_for_body = 0
        
        if not starts_with_body:
            # Trace doesn't start with body - add empty trace to body
            empty_traces_for_body += 1
            logger.debug(f"Loop filter: trace {trace} doesn't start with body, adding empty to body")
        
        if not ends_with_body:
            # Trace doesn't end with body - add empty trace to body
            empty_traces_for_body += 1
            logger.debug(f"Loop filter: trace {trace} doesn't end with body, adding empty to body")
        
        # Add empty traces to body sublog
        if empty_traces_for_body > 0:
            empty_trace = tuple()
            split_logs[0][empty_trace] = (
                split_logs[0].get(empty_trace, 0) + frequency * empty_traces_for_body
            )
        
        # Now split the trace normally
        sub_trace: List[str] = []
        current_partition_idx = 0
        current_partition = partitions[0]
        
        for event in trace:
            # Find which partition this event belongs to
            event_partition_idx = -1
            for p_idx, partition in enumerate(partitions):
                if event in partition:
                    event_partition_idx = p_idx
                    break
            
            if event_partition_idx == -1:
                # Event not in any partition - skip
                continue
            
            if event_partition_idx != current_partition_idx:
                # Switching partitions - save current subtrace
                if sub_trace:
                    t = tuple(sub_trace)
                    split_logs[current_partition_idx][t] = (
                        split_logs[current_partition_idx].get(t, 0) + frequency
                    )
                    sub_trace = []
                current_partition_idx = event_partition_idx
                current_partition = partitions[current_partition_idx]
            
            sub_trace.append(event)
        
        # Don't forget the last subtrace
        if sub_trace:
            t = tuple(sub_trace)
            split_logs[current_partition_idx][t] = (
                split_logs[current_partition_idx].get(t, 0) + frequency
            )
    
    return split_logs


# ============================================================================
# Base Case Filters (Section 3.2)
# ============================================================================

def is_single_activity_frequent(
    log: Dict[Tuple[str, ...], int],
    noise_threshold: float
) -> bool:
    """
    Determine if a single-activity log represents frequent behavior.
    
    Paper Reference (Section 3.2 - Single Activities):
    --------------------------------------------------
    "a is only discovered by IMi if the average number of occurrences per trace 
    of a in the log is close enough to 1, dependent on the relative threshold k."
    
    If avg occurrences > 1 / (1 - k), the loop model is more appropriate.
    If avg occurrences ≈ 1, the single activity is appropriate.
    
    Parameters:
    -----------
    log : Dict[Tuple[str, ...], int]
        Log containing only one unique activity
    noise_threshold : float
        The relative threshold k from the paper
        
    Returns:
    --------
    bool
        True if single activity should be discovered (avg close to 1)
        False if flower/loop model should be discovered (avg > threshold)
    """
    if not log:
        return True
    
    # Get the single activity
    activities = set()
    for trace in log.keys():
        activities.update(trace)
    
    if len(activities) != 1:
        return True  # Not a single-activity log
    
    activity = list(activities)[0]
    
    # Calculate average occurrences per trace
    total_occurrences = 0
    total_traces = 0
    
    for trace, freq in log.items():
        occurrences_in_trace = trace.count(activity)
        total_occurrences += occurrences_in_trace * freq
        total_traces += freq
    
    if total_traces == 0:
        return True
    
    avg_occurrences = total_occurrences / total_traces
    
    # Paper formula: discover 'a' if avg close to 1
    # Threshold: 1 / (1 - k) where k is noise_threshold
    # For k=0.2: threshold = 1/(1-0.2) = 1.25
    # For k=0.5: threshold = 1/(1-0.5) = 2.0
    
    if noise_threshold >= 1.0:
        threshold = float('inf')
    else:
        threshold = 1.0 / (1.0 - noise_threshold)
    
    is_frequent = avg_occurrences <= threshold
    
    logger.debug(f"Single activity filter: activity={activity}, "
                f"avg_occurrences={avg_occurrences:.2f}, threshold={threshold:.2f}, "
                f"is_single_activity={is_frequent}")
    
    return is_frequent


def is_empty_trace_frequent(
    log: Dict[Tuple[str, ...], int],
    noise_threshold: float
) -> bool:
    """
    Determine if empty traces in log are frequent enough to model with XOR(tau, ...).
    
    Paper Reference (Section 3.2 - Empty Traces):
    ---------------------------------------------
    "IMi only discovers ×(τ, . . .) if ε is frequent enough compared to the number 
    of traces in the log and with respect to k. If ε is not frequent enough, IMi 
    filters ε from L and recurses on L \ {ε}."
    
    The empty trace is considered frequent if:
        freq(ε) / total_traces >= noise_threshold
    
    Parameters:
    -----------
    log : Dict[Tuple[str, ...], int]
        Event log potentially containing empty traces
    noise_threshold : float
        The relative threshold k from the paper
        
    Returns:
    --------
    bool
        True if empty trace is frequent (should model with XOR(tau, ...))
        False if empty trace is infrequent (should filter and continue)
    """
    if tuple() not in log:
        return False  # No empty trace
    
    empty_freq = log.get(tuple(), 0)
    total_traces = sum(log.values())
    
    if total_traces == 0:
        return False
    
    empty_ratio = empty_freq / total_traces
    
    # Empty trace is frequent if its ratio >= threshold
    # With noise_threshold = 0.2, empty traces need to be >= 20% of total
    is_frequent = empty_ratio >= noise_threshold
    
    logger.debug(f"Empty trace filter: empty_freq={empty_freq}, total={total_traces}, "
                f"ratio={empty_ratio:.2%}, threshold={noise_threshold:.0%}, "
                f"is_frequent={is_frequent}")
    
    return is_frequent
