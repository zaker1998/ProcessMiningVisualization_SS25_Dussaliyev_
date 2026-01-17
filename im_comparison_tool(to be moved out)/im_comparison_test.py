"""
Inductive Miner Infrequent (IMf) Comparison Tool: Custom Implementation vs PM4Py

This standalone script compares our IMf implementation against PM4Py's reference
implementation to validate algorithm correctness.

IMPORTANT: This tool is intentionally separate from the main project.
PM4Py should NOT be added as a dependency to the main project.
This comparison tool can be moved to a separate repository in the future.

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
from typing import Dict, Tuple, Any, List
from dataclasses import dataclass

# Suppress logger output for cleaner comparison output
logging.getLogger("InductiveMining").setLevel(logging.WARNING)
logging.getLogger("InductiveMiningInfrequent").setLevel(logging.WARNING)

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import custom implementation
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
# PROCESS TREE EQUALITY (handles unordered operators like XOR, PAR)
# =============================================================================

def isProcessTreeEqual(tree1: Any, tree2: Any) -> bool:
    """
    Check if two process trees are structurally equal.
    
    Handles unordered operators (xor, par) where children can appear in any order,
    and ordered operators (seq, loop) where order matters.
    
    Example: xor(A, B) == xor(B, A) -> True
    """
    if type(tree1) != type(tree2):
        return False

    if isinstance(tree1, str) or isinstance(tree1, int):
        return tree1 == tree2

    if not isinstance(tree1, tuple):
        return False

    if len(tree1) != len(tree2):
        return False

    operation = tree1[0]
    if operation != tree2[0]:
        return False

    # Ordered cuts - sequence must match exactly
    if operation == "seq":
        return all(isProcessTreeEqual(tree1[i], tree2[i]) for i in range(1, len(tree1)))
    
    # Loop - first child (body) must match exactly, rest are unordered
    if operation == "loop":
        if not isProcessTreeEqual(tree1[1], tree2[1]):
            return False

    # Unordered cuts (xor, par, and loop redo parts) - children can appear in any order
    for i in range(1, len(tree1)):
        foundEqual = False
        for j in range(1, len(tree2)):
            if isProcessTreeEqual(tree1[i], tree2[j]):
                foundEqual = True
                break
        if not foundEqual:
            return False

    return True


def format_tree(tree: Any, max_len: int = 80) -> str:
    """Format tree string with truncation if too long."""
    tree_str = str(tree)
    if len(tree_str) > max_len:
        return tree_str[:max_len] + "..."
    return tree_str


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

def run_custom_imf(log: Dict[Tuple[str, ...], int], noise_threshold: float = 0.2) -> Any:
    """Run custom Inductive Miner - Infrequent."""
    miner = InductiveMiningInfrequent(log)
    miner.noise_threshold = noise_threshold
    return miner.inductive_mining(log)


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
    """Result of comparing custom IMf vs PM4Py IMf."""
    log_name: str
    noise_threshold: float
    custom_tree: Any
    pm4py_tree: Any
    is_equal: bool  # Using isProcessTreeEqual
    custom_error: str | None = None
    pm4py_error: str | None = None


# =============================================================================
# MAIN COMPARISON
# =============================================================================

def compare_single_log(log_name: str, log: Dict[Tuple[str, ...], int], noise_threshold: float = 0.2) -> ComparisonResult:
    """Run IMf comparison for a single log."""
    custom_tree = None
    pm4py_tree = None
    custom_error = None
    pm4py_error = None
    
    # Run custom implementation
    try:
        custom_tree = run_custom_imf(log, noise_threshold)
    except Exception as e:
        custom_error = str(e)
    
    # Run PM4Py implementation
    if PM4PY_AVAILABLE:
        try:
            pm4py_tree = run_pm4py_imf(log, noise_threshold)
        except Exception as e:
            pm4py_error = str(e)
    else:
        pm4py_error = "PM4Py not installed"
    
    # Compare using isProcessTreeEqual
    is_equal = False
    if custom_tree is not None and pm4py_tree is not None:
        is_equal = isProcessTreeEqual(custom_tree, pm4py_tree)
    
    return ComparisonResult(
        log_name=log_name,
        noise_threshold=noise_threshold,
        custom_tree=custom_tree,
        pm4py_tree=pm4py_tree,
        is_equal=is_equal,
        custom_error=custom_error,
        pm4py_error=pm4py_error,
    )


def run_all_comparisons(noise_threshold: float = 0.2) -> List[ComparisonResult]:
    """Run IMf comparison on all test logs."""
    results = []
    for log_name, log in TEST_LOGS.items():
        result = compare_single_log(log_name, log, noise_threshold)
        results.append(result)
    return results


def print_results(results: List[ComparisonResult]):
    """Print comparison results in a clean format."""
    print("\n" + "=" * 90)
    print("IMf COMPARISON RESULTS: Custom Implementation vs PM4Py")
    print("=" * 90)
    
    total = len(results)
    equal_count = sum(1 for r in results if r.is_equal)
    
    print(f"\nNoise Threshold: {results[0].noise_threshold if results else 0.2}")
    print(f"Total Tests: {total}")
    print(f"Equal (using isProcessTreeEqual): {equal_count}/{total} ({equal_count/total*100:.0f}%)")
    
    print(f"\n{'Log Name':<25} | {'Equal?':^8} | {'Custom Tree':<40}")
    print(f"{'-' * 25}-+-{'-' * 8}-+-{'-' * 40}")
    
    for r in results:
        status = "✅" if r.is_equal else "❌"
        if r.custom_error:
            tree_str = f"ERROR: {r.custom_error}"
        else:
            tree_str = format_tree(r.custom_tree, 40)
        print(f"{r.log_name[:25]:<25} | {status:^8} | {tree_str}")
    
    # Show details for mismatches
    mismatches = [r for r in results if not r.is_equal and r.custom_tree and r.pm4py_tree]
    if mismatches:
        print(f"\n{'=' * 90}")
        print("MISMATCH DETAILS")
        print("=" * 90)
        for r in mismatches:
            print(f"\n[{r.log_name}]")
            print(f"  Custom: {format_tree(r.custom_tree, 80)}")
            print(f"  PM4Py:  {format_tree(r.pm4py_tree, 80)}")


def run_threshold_comparison():
    """Compare results across different noise thresholds."""
    print("\n" + "=" * 90)
    print("NOISE THRESHOLD COMPARISON")
    print("=" * 90)
    
    thresholds = [0.0, 0.1, 0.2, 0.3, 0.5]
    
    print(f"\n{'Threshold':>10} | {'Equal/Total':>12} | {'Match Rate':>10}")
    print(f"{'-' * 10}-+-{'-' * 12}-+-{'-' * 10}")
    
    for threshold in thresholds:
        results = run_all_comparisons(threshold)
        equal_count = sum(1 for r in results if r.is_equal)
        total = len(results)
        rate = equal_count / total * 100 if total > 0 else 0
        print(f"{threshold:>10.2f} | {equal_count:>5}/{total:<5} | {rate:>9.0f}%")


def main():
    """Main entry point."""
    print("\n" + "=" * 90)
    print("INDUCTIVE MINER INFREQUENT (IMf) COMPARISON TOOL")
    print("Comparing Custom Implementation vs PM4Py Reference")
    print("Using isProcessTreeEqual for structural comparison (handles xor(A,B) == xor(B,A))")
    print("=" * 90)
    
    if not PM4PY_AVAILABLE:
        print("\n❌ PM4Py not installed - cannot run comparison")
        print("   Install with: pip install pm4py")
        return
    
    print(f"\n✅ PM4Py version: {pm4py.__version__}")
    
    # Run main comparison with default threshold
    results = run_all_comparisons(noise_threshold=0.2)
    print_results(results)
    
    # Run threshold comparison
    run_threshold_comparison()
    
    print("\n" + "=" * 90)
    print("COMPARISON COMPLETE")
    print("=" * 90 + "\n")
    
    return results


if __name__ == "__main__":
    main()
