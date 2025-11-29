"""
Inductive Miner Comparison Tool: Custom Implementation vs PM4Py

This script compares the custom inductive miner implementations against PM4Py's
reference implementations. It tests:
- Standard Inductive Miner (IM)
- Inductive Miner - Directly-Follows (IMd)
- Inductive Miner - Infrequent (IMf)

Usage:
    cd Process_Mining_Visualisation
    set PYTHONPATH=src
    python "im_comparison_tool(to be moved out)/im_comparison_test.py"
"""

import sys
import os
from typing import Dict, Tuple, Set, Any

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import custom implementations
from core.algorithms.inductive import InductiveMining
from core.algorithms.inductive_df import InductiveMiningDF
from core.algorithms.inductive_infrequent import InductiveMiningInfrequent

# Try to import PM4Py
try:
    import pm4py
    from pm4py.objects.log.obj import EventLog, Trace, Event
    from pm4py.algo.discovery.inductive import algorithm as inductive_miner
    PM4PY_AVAILABLE = True
except ImportError:
    PM4PY_AVAILABLE = False


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
    """Extract all activities from a process tree."""
    if isinstance(tree, str):
        return {tree} if tree != 'tau' else set()
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
    if isinstance(tree, tuple):
        return 1 + sum(count_nodes(child) for child in tree[1:])
    return 0


def get_depth(tree: Any) -> int:
    """Get maximum depth of a process tree."""
    if isinstance(tree, str):
        return 1
    if isinstance(tree, tuple) and len(tree) > 1:
        return 1 + max(get_depth(child) for child in tree[1:])
    return 1


def format_tree(tree: Any, max_len: int = 70) -> str:
    """Format tree string with truncation if too long."""
    tree_str = str(tree)
    if len(tree_str) > max_len:
        return tree_str[:max_len] + "..."
    return tree_str


def trees_match(tree1: Any, tree2: Any) -> str:
    """Compare two trees and return match status."""
    if str(tree1) == str(tree2):
        return "✓ IDENTICAL"
    acts1, acts2 = get_activities(tree1), get_activities(tree2)
    if acts1 == acts2:
        return "≈ Same activities, different structure"
    return "✗ Different"


# =============================================================================
# TEST LOGS
# =============================================================================

TEST_LOGS = {
    "Sequential (A→B→C)": {
        ("A", "B", "C"): 100,
    },
    
    "Parallel (A∥B)": {
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


def run_custom_imd(log: Dict[Tuple[str, ...], int]) -> Any:
    """Run custom Inductive Miner - Directly-Follows."""
    miner = InductiveMiningDF(log)
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


def run_pm4py_imd(log: Dict[Tuple[str, ...], int]) -> Any:
    """Run PM4Py Inductive Miner - Directly-Follows."""
    pm4py_log = log_to_pm4py(log)
    tree = inductive_miner.apply(pm4py_log, variant=inductive_miner.Variants.IMd)
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
# MAIN COMPARISON
# =============================================================================

def compare_single_log(log_name: str, log: Dict[Tuple[str, ...], int], noise_threshold: float = 0.2):
    """Run comparison for a single log."""
    print(f"\n{'─' * 80}")
    print(f"LOG: {log_name}")
    print(f"     Traces: {len(log)} unique, {sum(log.values())} total")
    print(f"{'─' * 80}")
    
    algorithms = [
        ("IM", run_custom_im, run_pm4py_im if PM4PY_AVAILABLE else None, {}),
        ("IMd", run_custom_imd, run_pm4py_imd if PM4PY_AVAILABLE else None, {}),
        ("IMf", run_custom_imf, run_pm4py_imf if PM4PY_AVAILABLE else None, {'noise_threshold': noise_threshold}),
    ]
    
    for algo_name, custom_fn, pm4py_fn, kwargs in algorithms:
        print(f"\n  [{algo_name}]")
        
        try:
            custom_tree = custom_fn(log, **kwargs) if kwargs else custom_fn(log)
            print(f"    CUSTOM:  {format_tree(custom_tree)}")
            print(f"             Nodes: {count_nodes(custom_tree)} | Depth: {get_depth(custom_tree)}")
        except Exception as e:
            print(f"    CUSTOM:  ERROR - {e}")
            custom_tree = None
        
        if pm4py_fn:
            try:
                pm4py_tree = pm4py_fn(log, **kwargs) if kwargs else pm4py_fn(log)
                print(f"    PM4PY:   {format_tree(pm4py_tree)}")
                print(f"             Nodes: {count_nodes(pm4py_tree)} | Depth: {get_depth(pm4py_tree)}")
                
                if custom_tree:
                    match_status = trees_match(custom_tree, pm4py_tree)
                    print(f"    COMPARE: {match_status}")
            except Exception as e:
                print(f"    PM4PY:   ERROR - {e}")
        elif not PM4PY_AVAILABLE:
            print(f"    PM4PY:   Not available (install with: pip install pm4py)")


def run_noise_threshold_test():
    """Test IMf with different noise thresholds."""
    print(f"\n{'=' * 80}")
    print("NOISE THRESHOLD TEST")
    print(f"{'=' * 80}")
    
    noisy_log = {
        ('A', 'B', 'C'): 100,
        ('A', 'C', 'B'): 100,
        ('A', 'X', 'B', 'C'): 3,  # Noise
        ('A', 'B', 'Y', 'C'): 2,  # Noise
    }
    
    print(f"\nLog: Main pattern A→(B∥C) with noise activities X, Y")
    print(f"Main traces: 200, Noisy traces: 5")
    
    for threshold in [0.0, 0.1, 0.2, 0.5]:
        print(f"\n  noise_threshold = {threshold}:")
        
        custom_tree = run_custom_imf(noisy_log, threshold)
        print(f"    CUSTOM: {format_tree(custom_tree)}")
        
        if PM4PY_AVAILABLE:
            pm4py_tree = run_pm4py_imf(noisy_log, threshold)
            print(f"    PM4PY:  {format_tree(pm4py_tree)}")
            print(f"    Match:  {trees_match(custom_tree, pm4py_tree)}")


def main():
    """Main entry point."""
    print("=" * 80)
    print("  INDUCTIVE MINER COMPARISON: Custom vs PM4Py")
    print("=" * 80)
    
    if PM4PY_AVAILABLE:
        print("\n[✓] PM4Py is installed - full comparison enabled")
    else:
        print("\n[!] PM4Py not installed - showing custom results only")
        print("    Install with: pip install pm4py")
    
    print("\nComparing implementations:")
    print("  • IM  - Standard Inductive Miner")
    print("  • IMd - Inductive Miner Directly-Follows")
    print("  • IMf - Inductive Miner Infrequent")
    
    # Run comparisons for all test logs
    print(f"\n{'=' * 80}")
    print("ALGORITHM COMPARISON ON TEST LOGS")
    print(f"{'=' * 80}")
    
    for log_name, log in TEST_LOGS.items():
        compare_single_log(log_name, log)
    
    # Noise threshold test
    run_noise_threshold_test()
    
    print(f"\n{'=' * 80}")
    print("COMPARISON COMPLETE")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
