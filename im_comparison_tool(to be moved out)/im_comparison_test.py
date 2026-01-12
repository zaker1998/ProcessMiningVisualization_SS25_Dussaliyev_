"""
Inductive Miner Comparison Tool: Custom Implementation vs PM4Py

This standalone script compares custom Inductive Miner implementations against
PM4Py's reference implementations to validate algorithm correctness.

IMPORTANT: This tool is intentionally separate from the main project.
PM4Py should NOT be added as a dependency to the main project.
This comparison tool can be moved to a separate repository in the future.

Compared Algorithms:
- Standard Inductive Miner (IM)
- Inductive Miner - Infrequent (IMf)

Usage:
    cd Process_Mining_Visualisation
    set PYTHONPATH=src
    python "im_comparison_tool(to be moved out)/im_comparison_test.py"
    
Requirements (for this tool only):
    pip install pm4py
"""

import sys
import os
import logging
import time
from typing import Dict, Tuple, Set, Any, Optional, List
from dataclasses import dataclass

# Suppress logger output for cleaner comparison output
logging.getLogger("InductiveMining").setLevel(logging.WARNING)
logging.getLogger("InductiveMiningInfrequent").setLevel(logging.WARNING)

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import custom implementations
from core.algorithms.inductive import InductiveMining
from core.algorithms.inductive_infrequent import InductiveMiningInfrequent

# Try to import PM4Py
try:
    import pm4py
    from pm4py.objects.log.obj import EventLog, Trace, Event
    from pm4py.algo.discovery.inductive import algorithm as inductive_miner
    PM4PY_AVAILABLE = True
except ImportError:
    PM4PY_AVAILABLE = False
    print("\n" + "=" * 70)
    print("ERROR: PM4Py is not installed!")
    print("This comparison tool requires PM4Py.")
    print("Install it with: pip install pm4py")
    print("=" * 70 + "\n")


# =============================================================================
# LOG FORMAT CONVERSION
# =============================================================================

def log_to_pm4py(log: Dict[Tuple[str, ...], int]) -> EventLog:
    """Convert custom log format {(trace): frequency} to PM4Py EventLog."""
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
# TREE ANALYSIS UTILITIES
# =============================================================================

def get_activities(tree: Any) -> Set[str]:
    """Extract all activities from a process tree (excluding 'tau')."""
    if isinstance(tree, str):
        return set() if tree == 'tau' else {tree}
    if isinstance(tree, (int, float)):
        return {str(tree)}
    if isinstance(tree, tuple):
        activities = set()
        for child in tree[1:]:
            activities.update(get_activities(child))
        return activities
    return set()


def count_nodes(tree: Any) -> int:
    """Count total nodes in a process tree."""
    if isinstance(tree, str):
        return 1
    if isinstance(tree, (int, float)):
        return 1
    if isinstance(tree, tuple) and len(tree) > 0:
        return 1 + sum(count_nodes(child) for child in tree[1:])
    return 1


def get_depth(tree: Any) -> int:
    """Get maximum depth of a process tree."""
    if isinstance(tree, str):
        return 1
    if isinstance(tree, (int, float)):
        return 1
    if isinstance(tree, tuple) and len(tree) > 1:
        return 1 + max(get_depth(child) for child in tree[1:])
    return 1


def count_operator(tree: Any, operator: str) -> int:
    """Count occurrences of a specific operator."""
    if isinstance(tree, (str, int, float)):
        return 0
    if isinstance(tree, tuple) and len(tree) > 0:
        count = 1 if tree[0] == operator else 0
        return count + sum(count_operator(child, operator) for child in tree[1:])
    return 0


def count_tau(tree: Any) -> int:
    """Count tau (silent transition) nodes."""
    if isinstance(tree, str):
        return 1 if tree == 'tau' else 0
    if isinstance(tree, (int, float)):
        return 0
    if isinstance(tree, tuple):
        return sum(count_tau(child) for child in tree[1:])
    return 0


def format_tree(tree: Any, max_len: int = 70) -> str:
    """Format tree string with truncation if too long."""
    tree_str = str(tree)
    if len(tree_str) > max_len:
        return tree_str[:max_len] + "..."
    return tree_str


def trees_match(tree1: Any, tree2: Any) -> str:
    """Compare two trees and return match status."""
    if str(tree1) == str(tree2):
        return "✅ IDENTICAL"
    acts1, acts2 = get_activities(tree1), get_activities(tree2)
    if acts1 == acts2:
        return "🔶 Same activities, different structure"
    return "❌ Different"


# =============================================================================
# TEST LOGS
# =============================================================================

TEST_LOGS = {
    "Sequential (A->B->C)": {
        ("A", "B", "C"): 100,
    },
    
    "Parallel (A||B)": {
        ("A", "B"): 50,
        ("B", "A"): 50,
    },
    
    "Choice (XOR)": {
        ("A", "B"): 50,
        ("A", "C"): 50,
    },
    
    "Loop (A*)": {
        ("A",): 30,
        ("A", "A"): 20,
        ("A", "A", "A"): 10,
    },
    
    "Complex Process": {
        ("A", "B", "C", "D"): 40,
        ("A", "C", "B", "D"): 35,
        ("A", "B", "E", "D"): 15,
        ("A", "C", "E", "D"): 10,
    },
    
    "Noisy Process": {
        ("A", "B", "C"): 100,
        ("A", "C", "B"): 100,
        ("A", "X", "B", "C"): 3,  # Noise
        ("A", "B", "Y", "C"): 2,  # Noise
    },
    
    "Order Process": {
        ("Receive", "Check", "Approve", "Ship", "Close"): 30,
        ("Receive", "Check", "Reject", "Close"): 10,
        ("Receive", "Check", "Approve", "Cancel", "Close"): 5,
    },
}


# =============================================================================
# COMPARISON FUNCTIONS
# =============================================================================

def run_custom_im(log: Dict[Tuple[str, ...], int]) -> Any:
    """Run custom Standard Inductive Miner."""
    miner = InductiveMining(log)
    return miner.inductive_mining(log)


def run_custom_imf(log: Dict[Tuple[str, ...], int], noise_threshold: float = 0.2) -> Any:
    """Run custom Inductive Miner - Infrequent."""
    miner = InductiveMiningInfrequent(log)
    miner.noise_threshold = noise_threshold
    return miner.inductive_mining(log)


def run_pm4py_im(log: Dict[Tuple[str, ...], int]) -> Any:
    """Run PM4Py Standard Inductive Miner."""
    pm4py_log = log_to_pm4py(log)
    tree = inductive_miner.apply(pm4py_log, variant=inductive_miner.Variants.IM)
    return pm4py_tree_to_tuple(tree)


def run_pm4py_imf(log: Dict[Tuple[str, ...], int], noise_threshold: float = 0.2) -> Any:
    """Run PM4Py Inductive Miner - Infrequent."""
    pm4py_log = log_to_pm4py(log)
    tree = inductive_miner.apply(
        pm4py_log,
        variant=inductive_miner.Variants.IMf,
        parameters={'noise_threshold': noise_threshold}
    )
    return pm4py_tree_to_tuple(tree)


# =============================================================================
# COMPARISON RESULT STORAGE
# =============================================================================

@dataclass
class ComparisonResult:
    """Result of comparing custom vs PM4Py for one algorithm."""
    algorithm: str
    log_name: str
    custom_tree: Any
    pm4py_tree: Any
    trees_identical: bool
    same_activities: bool
    custom_time_ms: float
    pm4py_time_ms: float
    custom_nodes: int
    pm4py_nodes: int
    custom_error: Optional[str] = None
    pm4py_error: Optional[str] = None


# =============================================================================
# MAIN COMPARISON
# =============================================================================

def compare_single_log(log_name: str, log: Dict[Tuple[str, ...], int], noise_threshold: float = 0.2) -> List[ComparisonResult]:
    """Run comparison for a single log."""
    print(f"\n{'=' * 80}")
    print(f"LOG: {log_name}")
    print(f"     Traces: {len(log)} unique, {sum(log.values())} total cases")
    print(f"{'=' * 80}")
    
    results = []
    
    algorithms = [
        ("Standard IM", run_custom_im, run_pm4py_im, {}),
        ("Infrequent IM", run_custom_imf, run_pm4py_imf, {'noise_threshold': noise_threshold}),
    ]
    
    for algo_name, custom_fn, pm4py_fn, kwargs in algorithms:
        print(f"\n  [{algo_name}] {'-' * 60}")
        
        custom_tree = None
        pm4py_tree = None
        custom_error = None
        pm4py_error = None
        custom_time = 0.0
        pm4py_time = 0.0
        
        # Run custom implementation
        try:
            start = time.perf_counter()
            custom_tree = custom_fn(log, **kwargs) if kwargs else custom_fn(log)
            custom_time = (time.perf_counter() - start) * 1000
            print(f"  CUSTOM:  {format_tree(custom_tree)}")
            print(f"           Nodes: {count_nodes(custom_tree)}, Depth: {get_depth(custom_tree)}, Time: {custom_time:.1f}ms")
        except Exception as e:
            custom_error = str(e)
            print(f"  CUSTOM:  ERROR - {e}")
        
        # Run PM4Py implementation
        if PM4PY_AVAILABLE:
            try:
                start = time.perf_counter()
                pm4py_tree = pm4py_fn(log, **kwargs) if kwargs else pm4py_fn(log)
                pm4py_time = (time.perf_counter() - start) * 1000
                print(f"  PM4PY:   {format_tree(pm4py_tree)}")
                print(f"           Nodes: {count_nodes(pm4py_tree)}, Depth: {get_depth(pm4py_tree)}, Time: {pm4py_time:.1f}ms")
            except Exception as e:
                pm4py_error = str(e)
                print(f"  PM4PY:   ERROR - {e}")
        else:
            pm4py_error = "PM4Py not installed"
            print(f"  PM4PY:   Not available")
        
        # Compare
        if custom_tree and pm4py_tree:
            match = trees_match(custom_tree, pm4py_tree)
            print(f"  MATCH:   {match}")
        
        # Store result
        trees_identical = str(custom_tree) == str(pm4py_tree) if custom_tree and pm4py_tree else False
        same_activities = get_activities(custom_tree) == get_activities(pm4py_tree) if custom_tree and pm4py_tree else False
        
        results.append(ComparisonResult(
            algorithm=algo_name,
            log_name=log_name,
            custom_tree=custom_tree,
            pm4py_tree=pm4py_tree,
            trees_identical=trees_identical,
            same_activities=same_activities,
            custom_time_ms=custom_time,
            pm4py_time_ms=pm4py_time,
            custom_nodes=count_nodes(custom_tree) if custom_tree else 0,
            pm4py_nodes=count_nodes(pm4py_tree) if pm4py_tree else 0,
            custom_error=custom_error,
            pm4py_error=pm4py_error,
        ))
    
    return results


def run_noise_threshold_test():
    """Test IMf with different noise thresholds."""
    print("\n" + "=" * 80)
    print("NOISE THRESHOLD SENSITIVITY ANALYSIS")
    print("=" * 80)
    
    noisy_log = {
        ('A', 'B', 'C'): 100,
        ('A', 'C', 'B'): 100,
        ('A', 'X', 'B', 'C'): 3,  # Noise
        ('A', 'B', 'Y', 'C'): 2,  # Noise
    }
    
    print("\nLog: Main pattern A -> (B || C) with noise activities X, Y")
    print("Main traces: 200  |  Noisy traces: 5")
    
    thresholds = [0.0, 0.1, 0.2, 0.3, 0.5]
    
    print(f"\n{'Threshold':>10} | {'Custom Nodes':>12} | {'PM4Py Nodes':>11} | {'Match':>20}")
    print(f"{'-' * 10}-+-{'-' * 12}-+-{'-' * 11}-+-{'-' * 20}")
    
    for threshold in thresholds:
        custom_tree = run_custom_imf(noisy_log, threshold)
        
        if PM4PY_AVAILABLE:
            pm4py_tree = run_pm4py_imf(noisy_log, threshold)
            match = "✅" if str(custom_tree) == str(pm4py_tree) else "❌"
            pm4py_nodes = count_nodes(pm4py_tree)
        else:
            match = "N/A"
            pm4py_nodes = "-"
        
        print(f"{threshold:>10.2f} | {count_nodes(custom_tree):>12} | {pm4py_nodes:>11} | {match:>20}")


def print_summary(all_results: List[ComparisonResult]):
    """Print summary table of all results."""
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    
    total = len(all_results)
    identical = sum(1 for r in all_results if r.trees_identical)
    same_acts = sum(1 for r in all_results if r.same_activities and not r.trees_identical)
    different = total - identical - same_acts
    
    print(f"\nTotal comparisons: {total}")
    print(f"  ✅ Identical:               {identical} ({identical/total*100:.0f}%)")
    print(f"  🔶 Same activities:         {same_acts} ({same_acts/total*100:.0f}%)")
    print(f"  ❌ Different:               {different} ({different/total*100:.0f}%)")
    
    print(f"\n{'Log':<25} | {'Algorithm':<15} | {'Match':>20} | {'Custom':>8} | {'PM4Py':>8}")
    print(f"{'-' * 25}-+-{'-' * 15}-+-{'-' * 20}-+-{'-' * 8}-+-{'-' * 8}")
    
    for r in all_results:
        if r.trees_identical:
            match = "✅ Identical"
        elif r.same_activities:
            match = "🔶 Same activities"
        else:
            match = "❌ Different"
        
        print(f"{r.log_name[:25]:<25} | {r.algorithm:<15} | {match:>20} | {r.custom_nodes:>8} | {r.pm4py_nodes:>8}")


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("INDUCTIVE MINER COMPARISON TOOL")
    print("Custom Implementation vs PM4Py Reference")
    print("=" * 80)
    
    if PM4PY_AVAILABLE:
        print("\n✅ PM4Py is installed - full comparison enabled")
        print(f"   PM4Py version: {pm4py.__version__}")
    else:
        print("\n❌ PM4Py not installed - showing custom results only")
        print("   Install with: pip install pm4py")
        return
    
    print("\nAlgorithms being compared:")
    print("  • Standard Inductive Miner (IM)")
    print("  • Inductive Miner - Infrequent (IMf)")
    
    # Run comparisons
    all_results = []
    for log_name, log in TEST_LOGS.items():
        results = compare_single_log(log_name, log)
        all_results.extend(results)
    
    # Print summary
    print_summary(all_results)
    
    # Noise threshold test
    run_noise_threshold_test()
    
    print("\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80 + "\n")
    
    return all_results


if __name__ == "__main__":
    main()
