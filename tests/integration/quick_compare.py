"""
Quick Comparison:Own Inductive Miners vs PM4Py

Run this script to see side-by-side comparison of own implementations
with PM4Py's inductive miner implementations.

Usage:
    cd Process_Mining_Visualisation
    set PYTHONPATH=src
    python tests/comparison/quick_compare.py
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Your custom implementations
from core.algorithms.inductive import InductiveMining
from core.algorithms.inductive_df import InductiveMiningDF
from core.algorithms.inductive_infrequent import InductiveMiningInfrequent

# PM4Py
try:
    import pm4py
    from pm4py.objects.log.obj import EventLog, Trace, Event
    from pm4py.algo.discovery.inductive import algorithm as inductive_miner
    PM4PY_AVAILABLE = True
except ImportError:
    PM4PY_AVAILABLE = False
    print("[!] PM4Py not installed. Install with: pip install pm4py")
    sys.exit(1)


def custom_log_to_pm4py(log):
    """Convert your log format {(trace): frequency} to PM4Py EventLog"""
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


def pm4py_tree_to_tuple(tree):
    """Convert PM4Py process tree to tuple format like yours"""
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


def compare_trees(custom_tree, pm4py_tree):
    """Compare two trees and return similarity assessment"""
    custom_str = str(custom_tree)
    pm4py_str = str(pm4py_tree)
    
    # Extract activities
    def get_activities(tree):
        if isinstance(tree, str):
            return {tree} if tree != 'tau' else set()
        if isinstance(tree, tuple):
            activities = set()
            for child in tree[1:]:
                activities.update(get_activities(child))
            return activities
        return set()
    
    custom_acts = get_activities(custom_tree)
    pm4py_acts = get_activities(pm4py_tree)
    
    # Check if same activities
    same_activities = custom_acts == pm4py_acts
    
    # Check if same structure (simplified)
    same_structure = custom_str == pm4py_str
    
    return {
        'same_structure': same_structure,
        'same_activities': same_activities,
        'custom_activities': custom_acts,
        'pm4py_activities': pm4py_acts,
    }


def run_comparison():
    """Run full comparison"""
    print("=" * 75)
    print("  COMPARISON: Your Inductive Miners vs PM4Py")
    print("=" * 75)
    
    # Test logs
    test_logs = {
        'Sequential (A→B→C)': {('A', 'B', 'C'): 100},
        'Parallel (A→(B∥C))': {('A', 'B', 'C'): 50, ('A', 'C', 'B'): 50},
        'Choice (A→XOR(B,C))': {('A', 'B'): 50, ('A', 'C'): 50},
        'Loop (A*)': {('A',): 30, ('A', 'A'): 20, ('A', 'A', 'A'): 10},
    }
    
    for log_name, log in test_logs.items():
        print(f"\n{'─' * 75}")
        print(f"[LOG] {log_name}")
        print(f"{'─' * 75}")
        
        # Convert to PM4Py format
        pm4py_log = custom_log_to_pm4py(log)
        
        # Standard IM comparison
        print("\n  Standard Inductive Miner (IM):")
        
        # Your IM
        start = time.time()
        im = InductiveMining(log)
        custom_tree = im.inductive_mining(log)
        custom_time = time.time() - start
        
        # PM4Py IM
        start = time.time()
        pm4py_tree = inductive_miner.apply(pm4py_log, variant=inductive_miner.Variants.IM)
        pm4py_tuple = pm4py_tree_to_tuple(pm4py_tree)
        pm4py_time = time.time() - start
        
        comparison = compare_trees(custom_tree, pm4py_tuple)
        
        print(f"    YOUR IM:   {custom_tree}")
        print(f"    PM4PY IM:  {pm4py_tuple}")
        print(f"    Match: {'✓ IDENTICAL' if comparison['same_structure'] else '≈ Similar activities' if comparison['same_activities'] else '✗ Different'}")
        print(f"    Time:  YOUR={custom_time*1000:.2f}ms, PM4PY={pm4py_time*1000:.2f}ms")
        
        # IMf comparison  
        print("\n  Inductive Miner - Infrequent (IMf):")
        
        # Your IMf
        start = time.time()
        imf = InductiveMiningInfrequent(log)
        imf.noise_threshold = 0.2
        custom_imf_tree = imf.inductive_mining(log)
        custom_time = time.time() - start
        
        # PM4Py IMf
        start = time.time()
        pm4py_imf_tree = inductive_miner.apply(
            pm4py_log, 
            variant=inductive_miner.Variants.IMf,
            parameters={'noise_threshold': 0.2}
        )
        pm4py_imf_tuple = pm4py_tree_to_tuple(pm4py_imf_tree)
        pm4py_time = time.time() - start
        
        comparison = compare_trees(custom_imf_tree, pm4py_imf_tuple)
        
        print(f"    YOUR IMf:  {custom_imf_tree}")
        print(f"    PM4PY IMf: {pm4py_imf_tuple}")
        print(f"    Match: {'✓ IDENTICAL' if comparison['same_structure'] else '≈ Similar activities' if comparison['same_activities'] else '✗ Different'}")
        print(f"    Time:  YOUR={custom_time*1000:.2f}ms, PM4PY={pm4py_time*1000:.2f}ms")

    # Noisy log comparison
    print(f"\n{'=' * 75}")
    print("  NOISY LOG COMPARISON (Testing noise filtering)")
    print(f"{'=' * 75}")
    
    noisy_log = {
        ('A', 'B', 'C'): 100,      # Main pattern
        ('A', 'C', 'B'): 100,      # Main pattern (parallel)
        ('A', 'X', 'B', 'C'): 3,   # Noise: X is infrequent
        ('A', 'B', 'Y', 'C'): 2,   # Noise: Y is infrequent
    }
    
    print(f"\nLog: Main pattern A→(B∥C) with noise activities X, Y")
    print(f"Total traces: {sum(noisy_log.values())}")
    print(f"Main traces: 200, Noisy traces: 5")
    
    pm4py_noisy = custom_log_to_pm4py(noisy_log)
    
    print(f"\n{'─' * 75}")
    print("IMf with different noise thresholds:")
    print(f"{'─' * 75}")
    
    for threshold in [0.0, 0.1, 0.2, 0.5]:
        print(f"\n  noise_threshold = {threshold}:")
        
        # Your IMf
        imf = InductiveMiningInfrequent(noisy_log)
        imf.noise_threshold = threshold
        custom_tree = imf.inductive_mining(noisy_log)
        
        # PM4Py IMf
        pm4py_tree = inductive_miner.apply(
            pm4py_noisy, 
            variant=inductive_miner.Variants.IMf,
            parameters={'noise_threshold': threshold}
        )
        pm4py_tuple = pm4py_tree_to_tuple(pm4py_tree)
        
        # Truncate long outputs
        custom_str = str(custom_tree)
        pm4py_str = str(pm4py_tuple)
        
        if len(custom_str) > 65:
            custom_str = custom_str[:65] + "..."
        if len(pm4py_str) > 65:
            pm4py_str = pm4py_str[:65] + "..."
            
        print(f"    YOUR IMf:  {custom_str}")
        print(f"    PM4PY IMf: {pm4py_str}")

    # Performance comparison
    print(f"\n{'=' * 75}")
    print("  PERFORMANCE COMPARISON")
    print(f"{'=' * 75}")
    
    # Generate larger log
    large_log = {}
    for i in range(100):
        large_log[('Start', 'A', 'B', 'End')] = large_log.get(('Start', 'A', 'B', 'End'), 0) + 10
        large_log[('Start', 'B', 'A', 'End')] = large_log.get(('Start', 'B', 'A', 'End'), 0) + 10
    
    print(f"\nLarge log: {sum(large_log.values())} trace instances")
    
    pm4py_large = custom_log_to_pm4py(large_log)
    
    # Benchmark
    iterations = 5
    
    # Your IM
    start = time.time()
    for _ in range(iterations):
        im = InductiveMining(large_log)
        im.inductive_mining(large_log)
    custom_avg = (time.time() - start) / iterations * 1000
    
    # PM4Py IM
    start = time.time()
    for _ in range(iterations):
        inductive_miner.apply(pm4py_large, variant=inductive_miner.Variants.IM)
    pm4py_avg = (time.time() - start) / iterations * 1000
    
    print(f"\n  Standard IM ({iterations} iterations avg):")
    print(f"    YOUR IM:   {custom_avg:.2f}ms")
    print(f"    PM4PY IM:  {pm4py_avg:.2f}ms")
    print(f"    Ratio:     {'YOUR is ' + f'{pm4py_avg/custom_avg:.1f}x faster' if custom_avg < pm4py_avg else 'PM4PY is ' + f'{custom_avg/pm4py_avg:.1f}x faster'}")
    
    print(f"\n{'=' * 75}")
    print("  COMPARISON COMPLETE")
    print(f"{'=' * 75}")


if __name__ == "__main__":
    run_comparison()
