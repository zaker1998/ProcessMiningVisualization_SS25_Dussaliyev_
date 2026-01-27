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
    - Uses greedy forward-pass approach
    
∧ (Parallel): No filtering needed
    - Any sequence of interleaved activities is valid
    - Reuses standard parallel_split from splits.py
    
↺ (Loop): Handle invalid loop starts/ends
    - Add empty traces to body sublog for traces not starting/ending with body activities
"""

from typing import Dict, Tuple, List, Set

from core.log_processing.splits import parallel_split, find_correct_partition
from utils.logger import get_logger

logger = get_logger("IMfSplits")


def exclusive_split_imf(
    log: Dict[Tuple[str, ...], int], 
    partitions: List[Set[str]]
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
    
    Parameters
    ----------
    log : Dict[Tuple[str, ...], int]
        Event log with traces and frequencies
    partitions : List[Set[str]]
        XOR partitions of activities
        
    Returns
    -------
    List[Dict[Tuple[str, ...], int]]
        Split sublogs, one per partition
    """
    split_logs: List[Dict[Tuple[str, ...], int]] = [{} for _ in range(len(partitions))]
    
    for trace, frequency in log.items():
        if not trace:
            continue
        
        # Count activities per partition
        partition_counts = [
            sum(1 for event in trace if event in partition)
            for partition in partitions
        ]
        
        max_count = max(partition_counts)
        if max_count == 0:
            logger.debug(f"Trace {trace} has no activities matching any partition - skipping")
            continue
        
        best_partition_idx = partition_counts.index(max_count)
        best_partition = partitions[best_partition_idx]
        
        # Check if trace has activities from multiple partitions
        if sum(1 for c in partition_counts if c > 0) > 1:
            # Filter: keep only activities from best partition
            filtered_trace = tuple(event for event in trace if event in best_partition)
            logger.debug(f"XOR filter: {trace} -> {filtered_trace} (partition {best_partition_idx})")
            
            if filtered_trace:
                split_logs[best_partition_idx][filtered_trace] = (
                    split_logs[best_partition_idx].get(filtered_trace, 0) + frequency
                )
        else:
            # Trace belongs entirely to one partition
            split_logs[best_partition_idx][trace] = (
                split_logs[best_partition_idx].get(trace, 0) + frequency
            )
    
    return split_logs


def sequence_split_imf(
    log: Dict[Tuple[str, ...], int], 
    partitions: List[Set[str]]
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
    Uses greedy forward-pass approach to assign events to partitions.
    
    Parameters
    ----------
    log : Dict[Tuple[str, ...], int]
        Event log with traces and frequencies
    partitions : List[Set[str]]
        Sequence partitions of activities (ordered)
        
    Returns
    -------
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
    
    Paper Reference (Section 3.3 - →):
    "Filtering infrequent behaviour is an optimisation problem: the trace is to be 
    split in the least-events-removing way."
    
    Uses dynamic programming to find the optimal split point between consecutive 
    partitions that maximizes the number of kept events.
    
    Parameters
    ----------
    trace : Tuple[str, ...]
        Input trace
    partitions : List[Set[str]]
        Ordered sequence partitions
        
    Returns
    -------
    List[Tuple[str, ...]]
        Subtraces for each partition
    """
    n = len(trace)
    m = len(partitions)
    
    if n == 0:
        return [tuple() for _ in range(m)]
    
    if m == 1:
        # Single partition: keep all events that belong to it
        sub_trace = tuple(e for e in trace if e in partitions[0])
        return [sub_trace]
    
    # Map each event to its partition index (-1 if not in any partition)
    event_partitions = []
    for event in trace:
        p_idx = -1
        for idx, partition in enumerate(partitions):
            if event in partition:
                p_idx = idx
                break
        event_partitions.append(p_idx)
    
    # Use DP to find optimal split points
    # dp[i][j] = max events we can keep considering trace[0:i] with current partition <= j
    # We need to find split points between partitions
    
    # For m partitions, we need m-1 split points
    # split_points[k] = index in trace where partition k+1 starts (0 <= k < m-1)
    # Events before split_points[0] go to partition 0
    # Events between split_points[k-1] and split_points[k] go to partition k
    
    # Count events for each partition in ranges
    # prefix_count[p][i] = count of events belonging to partition p in trace[0:i]
    prefix_count = [[0] * (n + 1) for _ in range(m)]
    for i, ep in enumerate(event_partitions):
        for p in range(m):
            prefix_count[p][i + 1] = prefix_count[p][i] + (1 if ep == p else 0)
    
    def count_in_range(partition: int, start: int, end: int) -> int:
        """Count events of partition in trace[start:end]."""
        return prefix_count[partition][end] - prefix_count[partition][start]
    
    # DP: dp[k][i] = max events kept when using partitions 0..k for trace[0:i]
    # Transition: dp[k][i] = max over all j <= i of (dp[k-1][j] + count_in_range(k, j, i))
    
    # Initialize: dp[0][i] = count of partition 0 events in trace[0:i]
    dp = [[0] * (n + 1) for _ in range(m)]
    parent = [[-1] * (n + 1) for _ in range(m)]  # For backtracking
    
    for i in range(n + 1):
        dp[0][i] = count_in_range(0, 0, i)
        parent[0][i] = 0  # Always starts at 0
    
    # Fill DP table
    for k in range(1, m):
        for i in range(n + 1):
            best_val = -1
            best_j = 0
            for j in range(i + 1):
                val = dp[k - 1][j] + count_in_range(k, j, i)
                if val > best_val:
                    best_val = val
                    best_j = j
            dp[k][i] = best_val
            parent[k][i] = best_j
    
    # Backtrack to find split points
    split_points = [0] * m  # split_points[k] = start index for partition k
    current_end = n
    for k in range(m - 1, 0, -1):
        split_points[k] = parent[k][current_end]
        current_end = split_points[k]
    split_points[0] = 0
    
    # Build subtraces based on split points
    sub_traces: List[List[str]] = [[] for _ in range(m)]
    for k in range(m):
        start = split_points[k]
        end = split_points[k + 1] if k < m - 1 else n
        for i in range(start, end):
            if event_partitions[i] == k:
                sub_traces[k].append(trace[i])
    
    return [tuple(st) for st in sub_traces]


# Parallel split needs no filtering - reuse from splits.py
parallel_split_imf = parallel_split


def loop_split_imf(
    log: Dict[Tuple[str, ...], int], 
    partitions: List[Set[str]]
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
    
    Parameters
    ----------
    log : Dict[Tuple[str, ...], int]
        Event log
    partitions : List[Set[str]]
        Loop partitions: [body, redo1, redo2, ...]
        
    Returns
    -------
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
        
        # Add empty traces to body for violations
        empty_traces_count = (0 if starts_with_body else 1) + (0 if ends_with_body else 1)
        
        if empty_traces_count > 0:
            empty_trace = tuple()
            split_logs[0][empty_trace] = (
                split_logs[0].get(empty_trace, 0) + frequency * empty_traces_count
            )
            logger.debug(f"Loop filter: trace {trace} violations, adding {empty_traces_count} empty to body")
        
        # Split the trace - switch partitions when event changes
        sub_trace: List[str] = []
        current_idx = 0
        
        for event in trace:
            event_idx, _ = find_correct_partition(event, partitions)
            
            if event_idx == -1:
                continue
            
            if event_idx != current_idx and sub_trace:
                # Switching partitions - save current subtrace
                t = tuple(sub_trace)
                split_logs[current_idx][t] = split_logs[current_idx].get(t, 0) + frequency
                sub_trace = []
                current_idx = event_idx
            elif event_idx != current_idx:
                current_idx = event_idx
            
            sub_trace.append(event)
        
        # Save last subtrace
        if sub_trace:
            t = tuple(sub_trace)
            split_logs[current_idx][t] = split_logs[current_idx].get(t, 0) + frequency
    
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
    
    The activity is frequent (single) if:
        lower_bound <= avg_occurrences <= upper_bound
    
    Where:
        - upper_bound = 1 / (1 - k) for k < 1, infinity for k = 1
        - lower_bound = 1 - k (activity must appear at least this often on average)
    
    Parameters
    ----------
    log : Dict[Tuple[str, ...], int]
        Log containing only one unique activity
    noise_threshold : float
        The relative threshold k from the paper (0.0 to 1.0)
        
    Returns
    -------
    bool
        True if single activity should be discovered (avg close to 1)
        False if flower/loop model should be discovered
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
    
    # Calculate bounds based on noise threshold
    # Upper bound: 1 / (1 - k) - allows more deviation at higher thresholds
    # Lower bound: 1 - k - activity must appear often enough
    
    if noise_threshold >= 1.0:
        upper_bound = float('inf')
    else:
        upper_bound = 1.0 / (1.0 - noise_threshold)
    
    lower_bound = 1.0 - noise_threshold
    
    # Activity is frequent if average is within bounds (close to 1)
    is_frequent = lower_bound <= avg_occurrences <= upper_bound
    
    logger.debug(f"Single activity filter: activity={activity}, "
                f"avg={avg_occurrences:.2f}, bounds=[{lower_bound:.2f}, {upper_bound:.2f}], "
                f"is_single={is_frequent}")
    
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
    filters ε from L and recurses on L without ε."
    
    The empty trace is considered frequent if:
        freq(ε) / total_traces > noise_threshold
    
    Parameters
    ----------
    log : Dict[Tuple[str, ...], int]
        Event log potentially containing empty traces
    noise_threshold : float
        The relative threshold k from the paper
        
    Returns
    -------
    bool
        True if empty trace is frequent (should model with XOR(tau, ...))
        False if empty trace is infrequent (should filter and continue)
    """
    if tuple() not in log:
        return False
    
    empty_freq = log.get(tuple(), 0)
    total_traces = sum(log.values())
    
    if total_traces == 0:
        return False
    
    empty_ratio = empty_freq / total_traces
    
    # Empty trace is frequent if ratio > threshold (strict inequality for pm4py match)
    is_frequent = empty_ratio > noise_threshold
    
    logger.debug(f"Empty trace filter: empty_freq={empty_freq}, total={total_traces}, "
                f"ratio={empty_ratio:.2%}, threshold={noise_threshold:.0%}, "
                f"is_frequent={is_frequent}")
    
    return is_frequent
