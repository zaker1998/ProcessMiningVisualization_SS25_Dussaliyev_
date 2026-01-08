"""
Inductive Miner Implementation Comparison: Custom vs PM4Py

This module compares custom Inductive Miner implementations against PM4Py's
reference implementations to validate algorithm correctness and quality.

Comparison Metrics:
-------------------
1. **Tree Structure Match**: Do both implementations produce the same process tree?
2. **Activity Coverage**: Do both discover the same activities?
3. **Structural Metrics**: Node count, depth, operator distribution
4. **Behavioral Equivalence**: Same activities with different structure

Supported Algorithms:
- Standard Inductive Miner (IM)
- Inductive Miner - Infrequent (IMf)

Usage:
------
    from core.analysis.algorithm_comparison import PM4PyComparator
    
    comparator = PM4PyComparator(log)
    results = comparator.compare_all()
    
Note: Requires PM4Py to be installed for comparison.
"""

from typing import Dict, Tuple, Any, List, Optional, Set
from dataclasses import dataclass, field
import time
from utils.logger import get_logger

logger = get_logger("AlgorithmComparison")

# Check if PM4Py is available
PM4PY_AVAILABLE = False
try:
    import pm4py
    from pm4py.objects.log.obj import EventLog, Trace, Event
    from pm4py.algo.discovery.inductive import algorithm as inductive_miner
    PM4PY_AVAILABLE = True
except ImportError:
    pass


@dataclass
class StructuralMetrics:
    """Structural metrics for a process tree."""
    node_count: int
    tree_depth: int
    activity_count: int
    tau_count: int
    seq_count: int
    xor_count: int
    par_count: int
    loop_count: int
    activities: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": self.node_count,
            "tree_depth": self.tree_depth,
            "activity_count": self.activity_count,
            "tau_count": self.tau_count,
            "seq_count": self.seq_count,
            "xor_count": self.xor_count,
            "par_count": self.par_count,
            "loop_count": self.loop_count,
            "activities": list(self.activities),
        }


@dataclass 
class ComparisonResult:
    """Result of comparing custom vs PM4Py implementation."""
    algorithm: str
    custom_tree: Any
    pm4py_tree: Any
    custom_metrics: Optional[StructuralMetrics]
    pm4py_metrics: Optional[StructuralMetrics]
    computation_time_custom_ms: float
    computation_time_pm4py_ms: float
    
    # Comparison verdicts
    trees_identical: bool = False
    same_activities: bool = False
    same_structure_type: bool = False  # Same operators at root level
    
    custom_error: Optional[str] = None
    pm4py_error: Optional[str] = None
    
    @property
    def match_status(self) -> str:
        """Get human-readable match status."""
        if self.custom_error:
            return f"❌ Custom Error: {self.custom_error}"
        if self.pm4py_error:
            return f"⚠️ PM4Py Error: {self.pm4py_error}"
        if self.trees_identical:
            return "✅ IDENTICAL"
        if self.same_activities:
            return "🔶 Same activities, different structure"
        return "❌ Different"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "custom_tree": str(self.custom_tree),
            "pm4py_tree": str(self.pm4py_tree),
            "custom_metrics": self.custom_metrics.to_dict() if self.custom_metrics else None,
            "pm4py_metrics": self.pm4py_metrics.to_dict() if self.pm4py_metrics else None,
            "computation_time_custom_ms": self.computation_time_custom_ms,
            "computation_time_pm4py_ms": self.computation_time_pm4py_ms,
            "trees_identical": self.trees_identical,
            "same_activities": self.same_activities,
            "match_status": self.match_status,
            "custom_error": self.custom_error,
            "pm4py_error": self.pm4py_error,
        }


@dataclass
class FullComparisonResult:
    """Full comparison results across all algorithms."""
    log_stats: Dict[str, Any]
    results: List[ComparisonResult]
    pm4py_available: bool
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_stats": self.log_stats,
            "results": [r.to_dict() for r in self.results],
            "pm4py_available": self.pm4py_available,
            "summary": self.summary,
        }


# =============================================================================
# TREE ANALYSIS UTILITIES  
# =============================================================================

def count_nodes(tree: Any) -> int:
    """Count total nodes in a process tree."""
    if isinstance(tree, str):
        return 1
    if isinstance(tree, (int, float)):
        return 1
    if isinstance(tree, tuple) and len(tree) > 0:
        return 1 + sum(count_nodes(child) for child in tree[1:])
    return 1


def get_tree_depth(tree: Any) -> int:
    """Get maximum depth of a process tree."""
    if isinstance(tree, str):
        return 1
    if isinstance(tree, (int, float)):
        return 1
    if isinstance(tree, tuple) and len(tree) > 1:
        return 1 + max(get_tree_depth(child) for child in tree[1:])
    return 1


def extract_activities(tree: Any) -> Set[str]:
    """Extract all activity names from a process tree (excluding 'tau')."""
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
    """Count tau (silent transition) nodes."""
    if isinstance(tree, str):
        return 1 if tree == 'tau' else 0
    if isinstance(tree, (int, float)):
        return 0
    if isinstance(tree, tuple):
        return sum(count_tau(child) for child in tree[1:])
    return 0


def count_operator(tree: Any, operator: str) -> int:
    """Count occurrences of a specific operator."""
    if isinstance(tree, (str, int, float)):
        return 0
    if isinstance(tree, tuple) and len(tree) > 0:
        count = 1 if tree[0] == operator else 0
        return count + sum(count_operator(child, operator) for child in tree[1:])
    return 0


def calculate_structural_metrics(tree: Any) -> StructuralMetrics:
    """Calculate all structural metrics for a process tree."""
    activities = extract_activities(tree)
    return StructuralMetrics(
        node_count=count_nodes(tree),
        tree_depth=get_tree_depth(tree),
        activity_count=len(activities),
        tau_count=count_tau(tree),
        seq_count=count_operator(tree, 'seq'),
        xor_count=count_operator(tree, 'xor'),
        par_count=count_operator(tree, 'par'),
        loop_count=count_operator(tree, 'loop'),
        activities=activities,
    )


# =============================================================================
# PM4PY CONVERSION UTILITIES
# =============================================================================

def log_to_pm4py(log: Dict[Tuple[str, ...], int]) -> "EventLog":
    """Convert custom log format {(trace): frequency} to PM4Py EventLog."""
    if not PM4PY_AVAILABLE:
        raise ImportError("PM4Py is not installed")
    
    event_log = EventLog()
    case_id = 0
    for trace_tuple, freq in log.items():
        for _ in range(freq):
            trace = Trace()
            trace.attributes['concept:name'] = str(case_id)
            for i, activity in enumerate(trace_tuple):
                event = Event()
                event['concept:name'] = str(activity)
                event['time:timestamp'] = i
                trace.append(event)
            event_log.append(trace)
            case_id += 1
    return event_log


def pm4py_tree_to_tuple(tree: Any) -> Any:
    """Convert PM4Py process tree to tuple format for comparison."""
    if tree is None:
        return 'tau'
    if tree.label is not None:
        return str(tree.label)
    if tree.operator is None:
        return 'tau'
    
    op_map = {
        pm4py.objects.process_tree.obj.Operator.SEQUENCE: 'seq',
        pm4py.objects.process_tree.obj.Operator.XOR: 'xor',
        pm4py.objects.process_tree.obj.Operator.PARALLEL: 'par',
        pm4py.objects.process_tree.obj.Operator.LOOP: 'loop',
    }
    op = op_map.get(tree.operator, str(tree.operator))
    children = tuple(pm4py_tree_to_tuple(c) for c in tree.children)
    return (op,) + children


# =============================================================================
# MAIN COMPARATOR CLASS
# =============================================================================

class PM4PyComparator:
    """
    Compare custom Inductive Miner implementations against PM4Py.
    
    This class validates that custom implementations produce correct
    results by comparing against the reference PM4Py implementations.
    """
    
    def __init__(self, log: Dict[Tuple[str, ...], int]):
        """
        Initialize comparator with an event log.
        
        Parameters
        ----------
        log : Dict[Tuple[str, ...], int]
            Event log as {trace: frequency}
        """
        self.log = log
        self.log_stats = self._calculate_log_stats()
        self.results: List[ComparisonResult] = []
        
    def _calculate_log_stats(self) -> Dict[str, Any]:
        """Calculate statistics about the input log."""
        traces = list(self.log.keys())
        activities = set()
        for trace in traces:
            activities.update(trace)
        
        total_events = sum(len(t) * f for t, f in self.log.items())
        total_cases = sum(self.log.values())
        
        return {
            "num_unique_traces": len(traces),
            "num_activities": len(activities),
            "total_events": total_events,
            "total_cases": total_cases,
            "activities": sorted(list(activities)),
        }
    
    @staticmethod
    def is_pm4py_available() -> bool:
        """Check if PM4Py is available."""
        return PM4PY_AVAILABLE
    
    def compare_standard_im(self) -> ComparisonResult:
        """Compare Standard Inductive Miner implementations."""
        from core.algorithms.inductive import InductiveMining
        
        custom_tree = None
        pm4py_tree = None
        custom_metrics = None
        pm4py_metrics = None
        custom_error = None
        pm4py_error = None
        custom_time = 0.0
        pm4py_time = 0.0
        
        # Run custom implementation
        try:
            start = time.perf_counter()
            miner = InductiveMining(self.log)
            custom_tree = miner.inductive_mining(self.log)
            custom_time = (time.perf_counter() - start) * 1000
            custom_metrics = calculate_structural_metrics(custom_tree)
        except Exception as e:
            custom_error = str(e)
            logger.error(f"Custom IM error: {e}")
        
        # Run PM4Py implementation
        if PM4PY_AVAILABLE:
            try:
                start = time.perf_counter()
                pm4py_log = log_to_pm4py(self.log)
                tree = inductive_miner.apply(pm4py_log, variant=inductive_miner.Variants.IM)
                pm4py_tree = pm4py_tree_to_tuple(tree)
                pm4py_time = (time.perf_counter() - start) * 1000
                pm4py_metrics = calculate_structural_metrics(pm4py_tree)
            except Exception as e:
                pm4py_error = str(e)
                logger.error(f"PM4Py IM error: {e}")
        else:
            pm4py_error = "PM4Py not installed"
        
        # Compare results
        trees_identical = str(custom_tree) == str(pm4py_tree) if custom_tree and pm4py_tree else False
        same_activities = (custom_metrics.activities == pm4py_metrics.activities 
                         if custom_metrics and pm4py_metrics else False)
        
        result = ComparisonResult(
            algorithm="Standard IM",
            custom_tree=custom_tree,
            pm4py_tree=pm4py_tree,
            custom_metrics=custom_metrics,
            pm4py_metrics=pm4py_metrics,
            computation_time_custom_ms=custom_time,
            computation_time_pm4py_ms=pm4py_time,
            trees_identical=trees_identical,
            same_activities=same_activities,
            custom_error=custom_error,
            pm4py_error=pm4py_error,
        )
        
        self.results.append(result)
        return result
    
    def compare_infrequent_im(self, noise_threshold: float = 0.2) -> ComparisonResult:
        """Compare Inductive Miner - Infrequent implementations."""
        from core.algorithms.inductive_infrequent import InductiveMiningInfrequent
        
        custom_tree = None
        pm4py_tree = None
        custom_metrics = None
        pm4py_metrics = None
        custom_error = None
        pm4py_error = None
        custom_time = 0.0
        pm4py_time = 0.0
        
        # Run custom implementation
        try:
            start = time.perf_counter()
            miner = InductiveMiningInfrequent(self.log)
            miner.noise_threshold = noise_threshold
            custom_tree = miner.inductive_mining(self.log)
            custom_time = (time.perf_counter() - start) * 1000
            custom_metrics = calculate_structural_metrics(custom_tree)
        except Exception as e:
            custom_error = str(e)
            logger.error(f"Custom IMf error: {e}")
        
        # Run PM4Py implementation
        if PM4PY_AVAILABLE:
            try:
                start = time.perf_counter()
                pm4py_log = log_to_pm4py(self.log)
                tree = inductive_miner.apply(
                    pm4py_log,
                    variant=inductive_miner.Variants.IMf,
                    parameters={'noise_threshold': noise_threshold}
                )
                pm4py_tree = pm4py_tree_to_tuple(tree)
                pm4py_time = (time.perf_counter() - start) * 1000
                pm4py_metrics = calculate_structural_metrics(pm4py_tree)
            except Exception as e:
                pm4py_error = str(e)
                logger.error(f"PM4Py IMf error: {e}")
        else:
            pm4py_error = "PM4Py not installed"
        
        # Compare results  
        trees_identical = str(custom_tree) == str(pm4py_tree) if custom_tree and pm4py_tree else False
        same_activities = (custom_metrics.activities == pm4py_metrics.activities
                         if custom_metrics and pm4py_metrics else False)
        
        result = ComparisonResult(
            algorithm=f"Infrequent IM (noise={noise_threshold})",
            custom_tree=custom_tree,
            pm4py_tree=pm4py_tree,
            custom_metrics=custom_metrics,
            pm4py_metrics=pm4py_metrics,
            computation_time_custom_ms=custom_time,
            computation_time_pm4py_ms=pm4py_time,
            trees_identical=trees_identical,
            same_activities=same_activities,
            custom_error=custom_error,
            pm4py_error=pm4py_error,
        )
        
        self.results.append(result)
        return result
    
    def compare_all(self, noise_threshold: float = 0.2) -> FullComparisonResult:
        """
        Run all comparisons.
        
        Parameters
        ----------
        noise_threshold : float
            Noise threshold for IMf comparison
            
        Returns
        -------
        FullComparisonResult
            Complete comparison results
        """
        self.results = []
        
        # Compare Standard IM
        self.compare_standard_im()
        
        # Compare IMf
        self.compare_infrequent_im(noise_threshold)
        
        # Generate summary
        summary = self._generate_summary()
        
        return FullComparisonResult(
            log_stats=self.log_stats,
            results=self.results,
            pm4py_available=PM4PY_AVAILABLE,
            summary=summary,
        )
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate comparison summary."""
        total = len(self.results)
        identical = sum(1 for r in self.results if r.trees_identical)
        same_activities = sum(1 for r in self.results if r.same_activities and not r.trees_identical)
        errors = sum(1 for r in self.results if r.custom_error or r.pm4py_error)
        
        return {
            "total_comparisons": total,
            "identical_trees": identical,
            "same_activities_different_structure": same_activities,
            "errors": errors,
            "match_rate": identical / total if total > 0 else 0.0,
            "compatibility_rate": (identical + same_activities) / total if total > 0 else 0.0,
        }
    
    def get_comparison_table(self) -> List[Dict[str, Any]]:
        """Get comparison data as table format for UI display."""
        table_data = []
        
        for result in self.results:
            row = {
                "Algorithm": result.algorithm,
                "Match": result.match_status,
                "Custom Nodes": result.custom_metrics.node_count if result.custom_metrics else "N/A",
                "PM4Py Nodes": result.pm4py_metrics.node_count if result.pm4py_metrics else "N/A",
                "Custom Depth": result.custom_metrics.tree_depth if result.custom_metrics else "N/A",
                "PM4Py Depth": result.pm4py_metrics.tree_depth if result.pm4py_metrics else "N/A",
                "Custom Time (ms)": f"{result.computation_time_custom_ms:.1f}",
                "PM4Py Time (ms)": f"{result.computation_time_pm4py_ms:.1f}",
            }
            table_data.append(row)
        
        return table_data
    
    def get_detailed_table(self) -> List[Dict[str, Any]]:
        """Get detailed structural comparison."""
        table_data = []
        
        for result in self.results:
            if result.custom_metrics:
                row = {
                    "Implementation": f"{result.algorithm} - Custom",
                    "Activities": result.custom_metrics.activity_count,
                    "Tau": result.custom_metrics.tau_count,
                    "Seq": result.custom_metrics.seq_count,
                    "XOR": result.custom_metrics.xor_count,
                    "Par": result.custom_metrics.par_count,
                    "Loop": result.custom_metrics.loop_count,
                }
                table_data.append(row)
            
            if result.pm4py_metrics:
                row = {
                    "Implementation": f"{result.algorithm} - PM4Py",
                    "Activities": result.pm4py_metrics.activity_count,
                    "Tau": result.pm4py_metrics.tau_count,
                    "Seq": result.pm4py_metrics.seq_count,
                    "XOR": result.pm4py_metrics.xor_count,
                    "Par": result.pm4py_metrics.par_count,
                    "Loop": result.pm4py_metrics.loop_count,
                }
                table_data.append(row)
        
        return table_data


# =============================================================================
# QUICK COMPARISON FUNCTION
# =============================================================================

def compare_with_pm4py(
    log: Dict[Tuple[str, ...], int],
    noise_threshold: float = 0.2
) -> Dict[str, Any]:
    """
    Quick comparison of custom implementations vs PM4Py.
    
    Parameters
    ----------
    log : Dict[Tuple[str, ...], int]
        Event log
    noise_threshold : float
        Noise threshold for IMf
        
    Returns
    -------
    Dict[str, Any]
        Comparison summary
    """
    comparator = PM4PyComparator(log)
    result = comparator.compare_all(noise_threshold)
    
    return {
        "log_stats": result.log_stats,
        "comparison_table": comparator.get_comparison_table(),
        "summary": result.summary,
        "pm4py_available": result.pm4py_available,
    }
