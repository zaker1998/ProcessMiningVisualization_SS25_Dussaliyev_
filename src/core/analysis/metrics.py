"""
Process Mining Quality Metrics - The "Four Devils" and Structural Metrics

This module implements comprehensive quality metrics for evaluating discovered process models:

**The Four Devils (Quality Dimensions):**
1. Fitness - How well does the model replay the log?
2. Precision - Does the model allow only observed behavior?
3. Generalization - Will the model work on unseen traces?
4. Simplicity - Is the model easy to understand?

**Structural Metrics:**
- Node count, tree depth, operator distribution
- Activity coverage, tau count
- Complexity measures

References:
-----------
- van der Aalst, W.M.P. (2016). Process Mining: Data Science in Action. Springer.
- Augusto et al. (2019). Automated Discovery of Process Models from Event Logs. IEEE TKDE.
"""

from typing import Dict, Tuple, Any, Set, List, Optional
from dataclasses import dataclass
import math


@dataclass
class QualityMetrics:
    """Container for all quality metrics."""
    # The Four Devils
    fitness: float
    precision: float
    generalization: float
    simplicity: float
    
    # F1 score (harmonic mean of fitness and precision)
    f1_score: float
    
    # Structural metrics
    node_count: int
    tree_depth: int
    activity_count: int
    tau_count: int
    
    # Operator distribution
    seq_count: int
    xor_count: int
    par_count: int
    loop_count: int
    
    # Derived metrics
    leaf_ratio: float  # leaves / total nodes
    operator_ratio: float  # operators / total nodes
    activity_coverage: float  # discovered activities / log activities
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "fitness": self.fitness,
            "precision": self.precision,
            "generalization": self.generalization,
            "simplicity": self.simplicity,
            "f1_score": self.f1_score,
            "node_count": self.node_count,
            "tree_depth": self.tree_depth,
            "activity_count": self.activity_count,
            "tau_count": self.tau_count,
            "seq_count": self.seq_count,
            "xor_count": self.xor_count,
            "par_count": self.par_count,
            "loop_count": self.loop_count,
            "leaf_ratio": self.leaf_ratio,
            "operator_ratio": self.operator_ratio,
            "activity_coverage": self.activity_coverage,
        }
    
    def __str__(self) -> str:
        """Pretty string representation."""
        return (
            f"Quality Metrics:\n"
            f"  Four Devils:\n"
            f"    Fitness:        {self.fitness:.4f}\n"
            f"    Precision:      {self.precision:.4f}\n"
            f"    Generalization: {self.generalization:.4f}\n"
            f"    Simplicity:     {self.simplicity:.4f}\n"
            f"    F1 Score:       {self.f1_score:.4f}\n"
            f"  Structural:\n"
            f"    Nodes:          {self.node_count}\n"
            f"    Depth:          {self.tree_depth}\n"
            f"    Activities:     {self.activity_count}\n"
            f"    Tau nodes:      {self.tau_count}\n"
            f"  Operators:\n"
            f"    Sequence:       {self.seq_count}\n"
            f"    XOR:            {self.xor_count}\n"
            f"    Parallel:       {self.par_count}\n"
            f"    Loop:           {self.loop_count}\n"
            f"  Ratios:\n"
            f"    Leaf ratio:     {self.leaf_ratio:.4f}\n"
            f"    Operator ratio: {self.operator_ratio:.4f}\n"
            f"    Activity coverage: {self.activity_coverage:.4f}"
        )


# =============================================================================
# STRUCTURAL METRICS (Tree Analysis)
# =============================================================================

def count_nodes(tree: Any) -> int:
    """
    Count total nodes in a process tree.
    
    Parameters
    ----------
    tree : Any
        Process tree (tuple or leaf)
        
    Returns
    -------
    int
        Total number of nodes
    """
    if isinstance(tree, str):
        return 1
    if isinstance(tree, (int, float)):
        return 1
    if isinstance(tree, tuple) and len(tree) > 0:
        return 1 + sum(count_nodes(child) for child in tree[1:])
    return 1


def get_tree_depth(tree: Any) -> int:
    """
    Get maximum depth of a process tree.
    
    Parameters
    ----------
    tree : Any
        Process tree
        
    Returns
    -------
    int
        Maximum depth (1 for leaf nodes)
    """
    if isinstance(tree, str):
        return 1
    if isinstance(tree, (int, float)):
        return 1
    if isinstance(tree, tuple) and len(tree) > 1:
        return 1 + max(get_tree_depth(child) for child in tree[1:])
    return 1


def extract_activities(tree: Any) -> Set[str]:
    """
    Extract all activity names from a process tree.
    
    Parameters
    ----------
    tree : Any
        Process tree
        
    Returns
    -------
    Set[str]
        Set of activity names (excluding 'tau')
    """
    if isinstance(tree, str):
        return set() if tree == 'tau' else {tree}
    if isinstance(tree, (int, float)):
        return {str(tree)}
    if isinstance(tree, tuple):
        activities = set()
        for child in tree[1:]:
            activities.update(extract_activities(child))
        return activities
    return set()


def count_tau(tree: Any) -> int:
    """
    Count tau (silent transition) nodes in a process tree.
    
    Parameters
    ----------
    tree : Any
        Process tree
        
    Returns
    -------
    int
        Number of tau nodes
    """
    if isinstance(tree, str):
        return 1 if tree == 'tau' else 0
    if isinstance(tree, (int, float)):
        return 0
    if isinstance(tree, tuple):
        return sum(count_tau(child) for child in tree[1:])
    return 0


def count_operator(tree: Any, operator: str) -> int:
    """
    Count occurrences of a specific operator in a process tree.
    
    Parameters
    ----------
    tree : Any
        Process tree
    operator : str
        Operator to count ('seq', 'xor', 'par', 'loop')
        
    Returns
    -------
    int
        Number of occurrences
    """
    if isinstance(tree, (str, int, float)):
        return 0
    if isinstance(tree, tuple) and len(tree) > 0:
        count = 1 if tree[0] == operator else 0
        return count + sum(count_operator(child, operator) for child in tree[1:])
    return 0


def get_operator_distribution(tree: Any) -> Dict[str, int]:
    """
    Get distribution of operators in a process tree.
    
    Parameters
    ----------
    tree : Any
        Process tree
        
    Returns
    -------
    Dict[str, int]
        Dictionary mapping operator names to counts
    """
    return {
        'seq': count_operator(tree, 'seq'),
        'xor': count_operator(tree, 'xor'),
        'par': count_operator(tree, 'par'),
        'loop': count_operator(tree, 'loop'),
    }


def count_leaves(tree: Any) -> int:
    """
    Count leaf nodes (activities and tau) in a process tree.
    
    Parameters
    ----------
    tree : Any
        Process tree
        
    Returns
    -------
    int
        Number of leaf nodes
    """
    if isinstance(tree, (str, int, float)):
        return 1
    if isinstance(tree, tuple):
        return sum(count_leaves(child) for child in tree[1:])
    return 1


# =============================================================================
# FITNESS METRICS
# =============================================================================

def calculate_trace_fitness(tree: Any, trace: Tuple[str, ...]) -> float:
    """
    Calculate fitness for a single trace against a process tree.
    
    Uses a simplified token-based replay approach.
    
    Parameters
    ----------
    tree : Any
        Process tree
    trace : Tuple[str, ...]
        Event trace
        
    Returns
    -------
    float
        Fitness score (0.0 to 1.0)
    """
    tree_activities = extract_activities(tree)
    trace_activities = set(trace)
    
    if len(trace) == 0:
        # Empty trace - check if model allows it (has tau or empty path)
        return 1.0 if _allows_empty_trace(tree) else 0.0
    
    # Simple fitness: what fraction of trace activities are in the model?
    if len(trace_activities) == 0:
        return 1.0
    
    covered = trace_activities.intersection(tree_activities)
    base_fitness = len(covered) / len(trace_activities)
    
    # Bonus for correct ordering (simplified check)
    order_bonus = _check_basic_ordering(tree, trace)
    
    return min(1.0, base_fitness * 0.8 + order_bonus * 0.2)


def _allows_empty_trace(tree: Any) -> bool:
    """Check if a tree can produce an empty trace."""
    if tree == 'tau':
        return True
    if isinstance(tree, str):
        return False
    if isinstance(tree, (int, float)):
        return False
    if isinstance(tree, tuple) and len(tree) > 0:
        op = tree[0]
        if op == 'xor':
            return any(_allows_empty_trace(child) for child in tree[1:])
        if op == 'loop':
            return _allows_empty_trace(tree[1]) if len(tree) > 1 else False
        if op == 'seq':
            return all(_allows_empty_trace(child) for child in tree[1:])
        if op == 'par':
            return all(_allows_empty_trace(child) for child in tree[1:])
    return False


def _check_basic_ordering(tree: Any, trace: Tuple[str, ...]) -> float:
    """
    Check if trace respects basic ordering constraints from tree.
    Returns a score between 0 and 1.
    """
    if len(trace) < 2:
        return 1.0
    
    # Extract sequence constraints
    seq_constraints = _extract_sequence_constraints(tree)
    
    if not seq_constraints:
        return 1.0
    
    # Check how many constraints are satisfied
    satisfied = 0
    for (a, b) in seq_constraints:
        if a in trace and b in trace:
            a_pos = trace.index(a)
            b_pos = trace.index(b)
            if a_pos < b_pos:
                satisfied += 1
            else:
                # Constraint violated
                pass
        else:
            # Activities not in trace, constraint doesn't apply
            satisfied += 1
    
    return satisfied / len(seq_constraints) if seq_constraints else 1.0


def _extract_sequence_constraints(tree: Any) -> List[Tuple[str, str]]:
    """Extract ordering constraints from sequence operators."""
    constraints = []
    
    if isinstance(tree, (str, int, float)):
        return constraints
    
    if isinstance(tree, tuple) and len(tree) > 1:
        op = tree[0]
        
        if op == 'seq':
            # Extract activities from each child in sequence
            for i in range(1, len(tree) - 1):
                left_activities = extract_activities(tree[i])
                right_activities = extract_activities(tree[i + 1])
                for a in left_activities:
                    for b in right_activities:
                        constraints.append((a, b))
        
        # Recurse into children
        for child in tree[1:]:
            constraints.extend(_extract_sequence_constraints(child))
    
    return constraints


def calculate_fitness(tree: Any, log: Dict[Tuple[str, ...], int]) -> float:
    """
    Calculate overall fitness of a process tree against an event log.
    
    Fitness measures how well the model can replay all traces in the log.
    
    Parameters
    ----------
    tree : Any
        Process tree
    log : Dict[Tuple[str, ...], int]
        Event log {trace: frequency}
        
    Returns
    -------
    float
        Overall fitness (0.0 to 1.0), weighted by trace frequency
    """
    if not log:
        return 1.0
    
    total_weight = sum(log.values())
    weighted_fitness = 0.0
    
    for trace, freq in log.items():
        trace_fitness = calculate_trace_fitness(tree, trace)
        weighted_fitness += trace_fitness * freq
    
    return weighted_fitness / total_weight if total_weight > 0 else 0.0


# =============================================================================
# PRECISION METRICS
# =============================================================================

def calculate_precision(tree: Any, log: Dict[Tuple[str, ...], int]) -> float:
    """
    Calculate precision of a process tree against an event log.
    
    Precision measures how much behavior the model allows beyond what's in the log.
    A model with high precision doesn't allow much extra behavior.
    
    Uses a simplified escaping edges approach.
    
    Parameters
    ----------
    tree : Any
        Process tree
    log : Dict[Tuple[str, ...], int]
        Event log
        
    Returns
    -------
    float
        Precision score (0.0 to 1.0)
    """
    tree_activities = extract_activities(tree)
    log_activities = set()
    observed_pairs = set()
    
    for trace in log.keys():
        log_activities.update(trace)
        for i in range(len(trace) - 1):
            observed_pairs.add((trace[i], trace[i + 1]))
    
    if not tree_activities:
        return 1.0
    
    # Check operator types - more restrictive operators = higher precision
    ops = get_operator_distribution(tree)
    
    # Calculate base precision from activity coverage
    if tree_activities:
        extra_activities = tree_activities - log_activities
        base_precision = 1.0 - (len(extra_activities) / len(tree_activities))
    else:
        base_precision = 1.0
    
    # Adjust for operator restrictiveness
    total_ops = sum(ops.values())
    if total_ops > 0:
        # XOR and SEQ are more restrictive than PAR and LOOP
        restrictive_ratio = (ops['seq'] + ops['xor']) / total_ops
        # Flowers (many loops/parallels) indicate low precision
        flower_penalty = 0.0
        if ops['loop'] > 0 and len(tree_activities) > 1:
            # Check for flower model pattern
            if _is_flower_model(tree):
                flower_penalty = 0.5
        
        precision = base_precision * (0.5 + 0.5 * restrictive_ratio) - flower_penalty
    else:
        precision = base_precision
    
    return max(0.0, min(1.0, precision))


def _is_flower_model(tree: Any) -> bool:
    """Check if tree is a flower model (loop with all activities as redo)."""
    if not isinstance(tree, tuple):
        return False
    if tree[0] != 'loop':
        return False
    if len(tree) < 2:
        return False
    
    # Flower model typically has tau or single activity as body
    # and many activities as redo parts
    body = tree[1]
    redo_count = len(tree) - 2
    
    if body == 'tau' and redo_count >= 2:
        return True
    if isinstance(body, str) and redo_count >= 2:
        return True
    
    return False


# =============================================================================
# GENERALIZATION METRICS
# =============================================================================

def calculate_generalization(tree: Any, log: Dict[Tuple[str, ...], int]) -> float:
    """
    Calculate generalization of a process tree.
    
    Generalization measures how well the model will perform on unseen traces.
    Uses a simplified k-fold cross-validation inspired approach.
    
    Parameters
    ----------
    tree : Any
        Process tree
    log : Dict[Tuple[str, ...], int]
        Event log
        
    Returns
    -------
    float
        Generalization score (0.0 to 1.0)
    """
    if not log:
        return 1.0
    
    # Get unique traces and their frequencies
    traces = list(log.keys())
    total_traces = len(traces)
    
    if total_traces <= 1:
        return 1.0  # Can't meaningfully measure with 1 trace
    
    # Calculate trace coverage and repetition
    total_events = sum(freq for freq in log.values())
    unique_ratio = total_traces / total_events if total_events > 0 else 1.0
    
    # Higher unique ratio = more diverse log = better generalization estimate
    # But also check if model is overfitting
    
    tree_activities = extract_activities(tree)
    log_activities = set()
    for trace in traces:
        log_activities.update(trace)
    
    # Model shouldn't have activities not in log (overfitting to nothing)
    # But also shouldn't be missing activities (underfitting)
    
    coverage = len(tree_activities.intersection(log_activities)) / len(log_activities) if log_activities else 1.0
    
    # Penalize flower models (they overfit to allowing anything)
    if _is_flower_model(tree):
        return max(0.0, 0.5 * coverage)
    
    # Balance between coverage and unique ratio
    generalization = 0.6 * coverage + 0.4 * (1.0 - unique_ratio)
    
    return max(0.0, min(1.0, generalization))


# =============================================================================
# SIMPLICITY METRICS
# =============================================================================

def calculate_simplicity(tree: Any, log: Optional[Dict[Tuple[str, ...], int]] = None) -> float:
    """
    Calculate simplicity of a process tree.
    
    Simplicity measures how easy the model is to understand.
    Based on structural complexity of the tree.
    
    Parameters
    ----------
    tree : Any
        Process tree
    log : Dict[Tuple[str, ...], int], optional
        Event log (used for relative complexity)
        
    Returns
    -------
    float
        Simplicity score (0.0 to 1.0)
    """
    nodes = count_nodes(tree)
    depth = get_tree_depth(tree)
    activities = len(extract_activities(tree))
    taus = count_tau(tree)
    
    # Calculate expected minimum size (at least one node per activity)
    expected_min_nodes = max(1, activities)
    
    # Node penalty: more nodes = less simple
    node_ratio = expected_min_nodes / nodes if nodes > 0 else 1.0
    
    # Depth penalty: deeper trees are harder to understand
    # A balanced tree of n activities has depth ~log2(n)
    expected_depth = max(1, math.ceil(math.log2(activities + 1))) if activities > 0 else 1
    depth_ratio = expected_depth / depth if depth > 0 else 1.0
    
    # Tau penalty: more silent transitions = less simple
    tau_penalty = 0.0
    if nodes > 0:
        tau_penalty = min(0.3, taus / nodes * 0.5)
    
    # Combine factors
    simplicity = 0.4 * node_ratio + 0.4 * depth_ratio + 0.2 * (1.0 - tau_penalty)
    
    return max(0.0, min(1.0, simplicity))


# =============================================================================
# COMBINED METRICS CALCULATION
# =============================================================================

def calculate_all_metrics(tree: Any, log: Dict[Tuple[str, ...], int]) -> QualityMetrics:
    """
    Calculate all quality metrics for a process tree and log.
    
    Parameters
    ----------
    tree : Any
        Process tree
    log : Dict[Tuple[str, ...], int]
        Event log
        
    Returns
    -------
    QualityMetrics
        Complete metrics object
    """
    # Calculate the Four Devils
    fitness = calculate_fitness(tree, log)
    precision = calculate_precision(tree, log)
    generalization = calculate_generalization(tree, log)
    simplicity = calculate_simplicity(tree, log)
    
    # F1 Score (harmonic mean of fitness and precision)
    if fitness + precision > 0:
        f1_score = 2 * (fitness * precision) / (fitness + precision)
    else:
        f1_score = 0.0
    
    # Structural metrics
    nodes = count_nodes(tree)
    depth = get_tree_depth(tree)
    activities = extract_activities(tree)
    tau_cnt = count_tau(tree)
    leaves = count_leaves(tree)
    
    # Operator distribution
    ops = get_operator_distribution(tree)
    
    # Log activities for coverage
    log_activities = set()
    for trace in log.keys():
        log_activities.update(trace)
    
    # Calculate ratios
    leaf_ratio = leaves / nodes if nodes > 0 else 1.0
    operator_ratio = (nodes - leaves) / nodes if nodes > 0 else 0.0
    activity_coverage = len(activities.intersection(log_activities)) / len(log_activities) if log_activities else 1.0
    
    return QualityMetrics(
        fitness=fitness,
        precision=precision,
        generalization=generalization,
        simplicity=simplicity,
        f1_score=f1_score,
        node_count=nodes,
        tree_depth=depth,
        activity_count=len(activities),
        tau_count=tau_cnt,
        seq_count=ops['seq'],
        xor_count=ops['xor'],
        par_count=ops['par'],
        loop_count=ops['loop'],
        leaf_ratio=leaf_ratio,
        operator_ratio=operator_ratio,
        activity_coverage=activity_coverage,
    )


def compare_trees(tree1: Any, tree2: Any, log: Dict[Tuple[str, ...], int]) -> Dict[str, Any]:
    """
    Compare two process trees and return comparative metrics.
    
    Parameters
    ----------
    tree1 : Any
        First process tree
    tree2 : Any
        Second process tree
    log : Dict[Tuple[str, ...], int]
        Event log for quality metrics
        
    Returns
    -------
    Dict[str, Any]
        Comparison results
    """
    metrics1 = calculate_all_metrics(tree1, log)
    metrics2 = calculate_all_metrics(tree2, log)
    
    # Check structural equivalence
    activities1 = extract_activities(tree1)
    activities2 = extract_activities(tree2)
    
    return {
        "tree1_metrics": metrics1.to_dict(),
        "tree2_metrics": metrics2.to_dict(),
        "same_activities": activities1 == activities2,
        "same_structure": str(tree1) == str(tree2),
        "fitness_diff": metrics1.fitness - metrics2.fitness,
        "precision_diff": metrics1.precision - metrics2.precision,
        "simplicity_diff": metrics1.simplicity - metrics2.simplicity,
        "node_count_diff": metrics1.node_count - metrics2.node_count,
        "depth_diff": metrics1.tree_depth - metrics2.tree_depth,
    }


def format_metrics_comparison(name1: str, metrics1: QualityMetrics, 
                              name2: str, metrics2: QualityMetrics) -> str:
    """
    Format a side-by-side comparison of two metrics objects.
    
    Parameters
    ----------
    name1 : str
        Name of first implementation
    metrics1 : QualityMetrics
        Metrics for first tree
    name2 : str
        Name of second implementation
    metrics2 : QualityMetrics
        Metrics for second tree
        
    Returns
    -------
    str
        Formatted comparison string
    """
    lines = [
        f"{'Metric':<20} {name1:>12} {name2:>12} {'Diff':>10}",
        "-" * 56,
        f"{'Fitness':<20} {metrics1.fitness:>12.4f} {metrics2.fitness:>12.4f} {metrics1.fitness - metrics2.fitness:>+10.4f}",
        f"{'Precision':<20} {metrics1.precision:>12.4f} {metrics2.precision:>12.4f} {metrics1.precision - metrics2.precision:>+10.4f}",
        f"{'Generalization':<20} {metrics1.generalization:>12.4f} {metrics2.generalization:>12.4f} {metrics1.generalization - metrics2.generalization:>+10.4f}",
        f"{'Simplicity':<20} {metrics1.simplicity:>12.4f} {metrics2.simplicity:>12.4f} {metrics1.simplicity - metrics2.simplicity:>+10.4f}",
        f"{'F1 Score':<20} {metrics1.f1_score:>12.4f} {metrics2.f1_score:>12.4f} {metrics1.f1_score - metrics2.f1_score:>+10.4f}",
        "-" * 56,
        f"{'Node Count':<20} {metrics1.node_count:>12d} {metrics2.node_count:>12d} {metrics1.node_count - metrics2.node_count:>+10d}",
        f"{'Tree Depth':<20} {metrics1.tree_depth:>12d} {metrics2.tree_depth:>12d} {metrics1.tree_depth - metrics2.tree_depth:>+10d}",
        f"{'Activities':<20} {metrics1.activity_count:>12d} {metrics2.activity_count:>12d} {metrics1.activity_count - metrics2.activity_count:>+10d}",
        f"{'Tau Count':<20} {metrics1.tau_count:>12d} {metrics2.tau_count:>12d} {metrics1.tau_count - metrics2.tau_count:>+10d}",
    ]
    return "\n".join(lines)
