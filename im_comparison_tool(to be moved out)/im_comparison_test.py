"""
Inductive Miner Comparison Tool: Custom Implementation vs PM4Py

Enhanced with the "Four Devils" quality metrics:
- Fitness: How well the model replays the log
- Precision: Does the model avoid extra behavior
- Generalization: Will it work on unseen traces
- Simplicity: Is the model easy to understand

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
import logging
from typing import Dict, Tuple, Set, Any, Optional
from dataclasses import dataclass

# Suppress logger output for cleaner comparison output
logging.getLogger("InductiveMining").setLevel(logging.WARNING)
logging.getLogger("InductiveMiningDF").setLevel(logging.WARNING)
logging.getLogger("InductiveMiningInfrequent").setLevel(logging.WARNING)

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import custom implementations
from core.algorithms.inductive import InductiveMining
from core.algorithms.inductive_df import InductiveMiningDF
from core.algorithms.inductive_infrequent import InductiveMiningInfrequent

# Import metrics module
from core.analysis.metrics import (
    QualityMetrics,
    calculate_all_metrics,
    calculate_fitness,
    calculate_precision,
    calculate_generalization,
    calculate_simplicity,
    count_nodes,
    get_tree_depth,
    extract_activities,
    count_tau,
    get_operator_distribution,
    format_metrics_comparison,
)

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
    return extract_activities(tree)


def get_depth(tree: Any) -> int:
    """Get maximum depth of a process tree."""
    return get_tree_depth(tree)


def format_tree(tree: Any, max_len: int = 70) -> str:
    """Format tree string with truncation if too long."""
    tree_str = str(tree)
    if len(tree_str) > max_len:
        return tree_str[:max_len] + "..."
    return tree_str


def trees_match(tree1: Any, tree2: Any) -> str:
    """Compare two trees and return match status."""
    if str(tree1) == str(tree2):
        return "[Y] IDENTICAL"
    acts1, acts2 = get_activities(tree1), get_activities(tree2)
    if acts1 == acts2:
        return "[~] Same activities, different structure"
    return "[X] Different"


def format_quality_badge(value: float) -> str:
    """Return a badge based on quality score."""
    if value >= 0.9:
        return f"[EXCELLENT] {value:.3f}"
    elif value >= 0.7:
        return f"[GOOD]      {value:.3f}"
    elif value >= 0.5:
        return f"[FAIR]      {value:.3f}"
    else:
        return f"[POOR]      {value:.3f}"


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
# METRICS DISPLAY
# =============================================================================

def print_four_devils(metrics: QualityMetrics, indent: str = "    "):
    """Print the Four Devils metrics in a formatted way."""
    print(f"{indent}+------------------------------------------------+")
    print(f"{indent}|           THE FOUR DEVILS                      |")
    print(f"{indent}+------------------------------------------------+")
    print(f"{indent}|  Fitness:        {format_quality_badge(metrics.fitness):>25} |")
    print(f"{indent}|  Precision:      {format_quality_badge(metrics.precision):>25} |")
    print(f"{indent}|  Generalization: {format_quality_badge(metrics.generalization):>25} |")
    print(f"{indent}|  Simplicity:     {format_quality_badge(metrics.simplicity):>25} |")
    print(f"{indent}+------------------------------------------------+")
    print(f"{indent}|  F1 Score:       {format_quality_badge(metrics.f1_score):>25} |")
    print(f"{indent}+------------------------------------------------+")


def print_structural_metrics(metrics: QualityMetrics, indent: str = "    "):
    """Print structural metrics."""
    print(f"{indent}Structural: Nodes={metrics.node_count} Depth={metrics.tree_depth} "
          f"Activities={metrics.activity_count} Taus={metrics.tau_count}")
    print(f"{indent}Operators:  seq={metrics.seq_count} xor={metrics.xor_count} "
          f"par={metrics.par_count} loop={metrics.loop_count}")


# =============================================================================
# MAIN COMPARISON
# =============================================================================

def compare_single_log(log_name: str, log: Dict[Tuple[str, ...], int], noise_threshold: float = 0.2):
    """Run comparison for a single log with full metrics."""
    print(f"\n{'=' * 80}")
    print(f"LOG: {log_name}")
    print(f"     Traces: {len(log)} unique, {sum(log.values())} total events")
    print(f"{'=' * 80}")
    
    algorithms = [
        ("IM", run_custom_im, run_pm4py_im if PM4PY_AVAILABLE else None, {}),
        ("IMd", run_custom_imd, run_pm4py_imd if PM4PY_AVAILABLE else None, {}),
        ("IMf", run_custom_imf, run_pm4py_imf if PM4PY_AVAILABLE else None, {'noise_threshold': noise_threshold}),
    ]
    
    results = []
    
    for algo_name, custom_fn, pm4py_fn, kwargs in algorithms:
        print(f"\n  +-- [{algo_name}] {'-' * 60}")
        
        custom_tree = None
        pm4py_tree = None
        custom_metrics = None
        pm4py_metrics = None
        
        # Run custom implementation
        try:
            custom_tree = custom_fn(log, **kwargs) if kwargs else custom_fn(log)
            custom_metrics = calculate_all_metrics(custom_tree, log)
            print(f"  |  CUSTOM:  {format_tree(custom_tree)}")
            print_structural_metrics(custom_metrics, "  |  ")
            print_four_devils(custom_metrics, "  |  ")
        except Exception as e:
            print(f"  |  CUSTOM:  ERROR - {e}")
        
        # Run PM4Py implementation
        if pm4py_fn:
            try:
                pm4py_tree = pm4py_fn(log, **kwargs) if kwargs else pm4py_fn(log)
                pm4py_metrics = calculate_all_metrics(pm4py_tree, log)
                print(f"  |")
                print(f"  |  PM4PY:   {format_tree(pm4py_tree)}")
                print_structural_metrics(pm4py_metrics, "  |  ")
                print_four_devils(pm4py_metrics, "  |  ")
                
                # Compare results
                if custom_tree and pm4py_tree:
                    match_status = trees_match(custom_tree, pm4py_tree)
                    print(f"  |")
                    print(f"  |  COMPARISON: {match_status}")
                    
                    if custom_metrics and pm4py_metrics:
                        print(f"  |  Metric Differences (Custom - PM4Py):")
                        print(f"  |    Fitness:    {custom_metrics.fitness - pm4py_metrics.fitness:+.4f}")
                        print(f"  |    Precision:  {custom_metrics.precision - pm4py_metrics.precision:+.4f}")
                        print(f"  |    Simplicity: {custom_metrics.simplicity - pm4py_metrics.simplicity:+.4f}")
                        
            except Exception as e:
                print(f"  |  PM4PY:   ERROR - {e}")
        elif not PM4PY_AVAILABLE:
            print(f"  |  PM4PY:   Not available (install with: pip install pm4py)")
        
        print(f"  +{'-' * 70}")
        
        results.append({
            'algorithm': algo_name,
            'custom_tree': custom_tree,
            'pm4py_tree': pm4py_tree,
            'custom_metrics': custom_metrics,
            'pm4py_metrics': pm4py_metrics,
        })
    
    return results


def run_noise_threshold_test():
    """Test IMf with different noise thresholds and show metrics."""
    print()
    print("=" * 90)
    print("||" + "  NOISE THRESHOLD SENSITIVITY ANALYSIS".center(86) + "||")
    print("=" * 90)
    
    noisy_log = {
        ('A', 'B', 'C'): 100,
        ('A', 'C', 'B'): 100,
        ('A', 'X', 'B', 'C'): 3,  # Noise
        ('A', 'B', 'Y', 'C'): 2,  # Noise
    }
    
    print()
    print("  Log Pattern: Main pattern A -> (B || C) with noise activities X, Y")
    print("  Main traces: 200   |   Noisy traces: 5")
    print()
    
    thresholds = [0.0, 0.1, 0.2, 0.5]
    
    # Header
    print(f"  {'Threshold':>10} | {'Fitness':>10} | {'Precision':>10} | {'Simplicity':>10} | {'Nodes':>6} | Tree Preview")
    print(f"  {'-' * 10}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 6}-+-{'-' * 28}")
    
    for threshold in thresholds:
        custom_tree = run_custom_imf(noisy_log, threshold)
        metrics = calculate_all_metrics(custom_tree, noisy_log)
        
        print(f"  {threshold:>10.2f} | {metrics.fitness:>10.4f} | {metrics.precision:>10.4f} | "
              f"{metrics.simplicity:>10.4f} | {metrics.node_count:>6d} | {format_tree(custom_tree, 28)}")
    
    print()
    
    if PM4PY_AVAILABLE:
        print()
        print(f"  {'-' * 86}")
        print("  PM4Py Comparison at Same Thresholds:")
        print(f"  {'-' * 86}")
        print(f"  {'Threshold':>10} | {'Fitness':>10} | {'Precision':>10} | {'Simplicity':>10} | {'Nodes':>6} | Tree Preview")
        print(f"  {'-' * 10}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 10}-+-{'-' * 6}-+-{'-' * 28}")
        
        for threshold in thresholds:
            pm4py_tree = run_pm4py_imf(noisy_log, threshold)
            metrics = calculate_all_metrics(pm4py_tree, noisy_log)
            
            print(f"  {threshold:>10.2f} | {metrics.fitness:>10.4f} | {metrics.precision:>10.4f} | "
                  f"{metrics.simplicity:>10.4f} | {metrics.node_count:>6d} | {format_tree(pm4py_tree, 28)}")


def print_summary_table(all_results: Dict[str, list]):
    """Print a summary table of all results."""
    print()
    print("=" * 105)
    print("||" + "  SUMMARY: FOUR DEVILS QUALITY METRICS".center(101) + "||")
    print("=" * 105)
    
    print()
    print(f"  {'Log Name':<25} | {'Algo':>5} | {'Fitness':>8} | {'Precision':>9} | {'General.':>8} | {'Simple':>8} | {'F1':>8} | {'Match':>6}")
    print(f"  {'-' * 25}-+-{'-' * 5}-+-{'-' * 8}-+-{'-' * 9}-+-{'-' * 8}-+-{'-' * 8}-+-{'-' * 8}-+-{'-' * 6}")
    
    for log_name, results in all_results.items():
        for i, result in enumerate(results):
            algo = result['algorithm']
            metrics = result['custom_metrics']
            
            if metrics:
                match = "N/A"
                if result['custom_tree'] and result['pm4py_tree']:
                    match = "Yes" if str(result['custom_tree']) == str(result['pm4py_tree']) else "~"
                
                log_display = log_name[:23] if i == 0 else ""
                print(f"  {log_display:<25} | {algo:>5} | {metrics.fitness:>8.4f} | {metrics.precision:>9.4f} | "
                      f"{metrics.generalization:>8.4f} | {metrics.simplicity:>8.4f} | {metrics.f1_score:>8.4f} | {match:>6}")
        
        print(f"  {'-' * 25}-+-{'-' * 5}-+-{'-' * 8}-+-{'-' * 9}-+-{'-' * 8}-+-{'-' * 8}-+-{'-' * 8}-+-{'-' * 6}")


def main():
    """Main entry point."""
    print()
    print("=" * 80)
    print("||" + " " * 76 + "||")
    print("||" + "  INDUCTIVE MINER COMPARISON TOOL".center(76) + "||")
    print("||" + "  with The Four Devils Quality Metrics".center(76) + "||")
    print("||" + " " * 76 + "||")
    print("=" * 80)
    
    if PM4PY_AVAILABLE:
        print("\n  [OK] PM4Py is installed - full comparison enabled")
    else:
        print("\n  [!!] PM4Py not installed - showing custom results only")
        print("       Install with: pip install pm4py")
    
    print()
    print("  Quality Metrics Legend:")
    print("  +---------------------------------------------------------+")
    print("  |  [EXCELLENT] >= 0.90   |   [GOOD] >= 0.70              |")
    print("  |  [FAIR]      >= 0.50   |   [POOR]  < 0.50              |")
    print("  +---------------------------------------------------------+")
    
    print()
    print("  Comparing Algorithms:")
    print("  +---------------------------------------------------------+")
    print("  |  IM  - Standard Inductive Miner                        |")
    print("  |  IMd - Inductive Miner Directly-Follows                |")
    print("  |  IMf - Inductive Miner Infrequent                      |")
    print("  +---------------------------------------------------------+")
    
    # Run comparisons for all test logs
    print()
    print("=" * 80)
    print("||" + "  ALGORITHM COMPARISON ON TEST LOGS".center(76) + "||")
    print("=" * 80)
    
    all_results = {}
    for log_name, log in TEST_LOGS.items():
        results = compare_single_log(log_name, log)
        all_results[log_name] = results
    
    # Print summary table
    print_summary_table(all_results)
    
    # Noise threshold test
    run_noise_threshold_test()
    
    print()
    print("=" * 80)
    print("||" + "  COMPARISON COMPLETE".center(76) + "||")
    print("=" * 80)
    print()
    
    # Return results for programmatic use
    return all_results


if __name__ == "__main__":
    main()
