import sys
import os
import pandas as pd
import pm4py
from pm4py.objects.log.obj import EventLog
from pm4py.objects.process_tree import semantics
from pm4py.visualization.process_tree import visualizer as pt_visualizer

# Add parent directory to import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our implementations
from mining_algorithms.inductive_mining import InductiveMining
from mining_algorithms.inductive_mining_infrequent import InductiveMiningInfrequent
from mining_algorithms.inductive_mining_approximate import InductiveMiningApproximate

def create_test_log():
    """Create a test log for comparing the algorithms."""
    # Define some test traces
    traces = [
        ['a', 'b', 'c', 'd'],          # Standard path
        ['a', 'c', 'b', 'd'],          # Parallel activities
        ['a', 'b', 'c', 'd'],          # Repeat of standard path
        ['a', 'c', 'd'],               # Skip an activity
        ['a', 'b', 'd'],               # Another skip
        ['a', 'e', 'd'],               # Infrequent path
        ['a', 'c', 'b', 'c', 'd'],     # Loop
        ['a', 'b', 'c', 'b', 'c', 'd'] # Complex loop
    ]
    
    # Convert to the format PM4Py expects
    event_log_pm4py = []
    for trace_idx, trace in enumerate(traces):
        events = []
        for event_idx, activity in enumerate(trace):
            events.append({
                'concept:name': activity,
                'time:timestamp': pd.Timestamp(2023, 1, 1, hour=event_idx),
                'case:concept:name': f'case_{trace_idx}'
            })
        event_log_pm4py.append(events)
    
    # Create log for our implementation
    log_dict = {}
    for trace in traces:
        trace_tuple = tuple(trace)
        if trace_tuple in log_dict:
            log_dict[trace_tuple] += 1
        else:
            log_dict[trace_tuple] = 1
    
    return EventLog(event_log_pm4py), log_dict

def compare_inductive_miners():
    """Compare the different inductive miner implementations."""
    # Create test logs
    pm4py_log, our_log = create_test_log()
    
    print("=== Testing Standard Inductive Miner ===")
    # PM4Py implementation
    pm4py_tree = pm4py.discovery.discover_process_tree_inductive(pm4py_log, noise_threshold=0.0)
    print(f"PM4Py Tree: {pm4py_tree}")
    
    # Our implementation
    our_miner = InductiveMining(our_log)
    our_miner.generate_graph(activity_threshold=0.0, traces_threshold=0.0)
    our_tree = our_miner.graph.process_tree
    print(f"Our Tree: {our_tree}")
    
    print("\n=== Testing Inductive Miner Infrequent (noise_threshold=0.2) ===")
    # PM4Py implementation
    pm4py_infreq_tree = pm4py.discovery.discover_process_tree_inductive(pm4py_log, noise_threshold=0.2)
    print(f"PM4Py Infrequent Tree: {pm4py_infreq_tree}")
    
    # Our implementation
    our_infreq_miner = InductiveMiningInfrequent(our_log)
    our_infreq_miner.generate_graph(activity_threshold=0.0, traces_threshold=0.0, noise_threshold=0.2)
    our_infreq_tree = our_infreq_miner.graph.process_tree
    print(f"Our Infrequent Tree: {our_infreq_tree}")
    
    print("\n=== Testing Approximate Inductive Miner ===")
    # Our implementation (no direct PM4Py equivalent)
    our_approx_miner = InductiveMiningApproximate(our_log)
    our_approx_miner.generate_graph(activity_threshold=0.0, traces_threshold=0.0, 
                                  simplification_threshold=0.2, min_bin_freq=0.1)
    our_approx_tree = our_approx_miner.graph.process_tree
    print(f"Our Approximate Tree: {our_approx_tree}")
    
    # Save visualizations
    try:
        # PM4Py trees
        pm4py_gviz = pt_visualizer.apply(pm4py_tree)
        pt_visualizer.save(pm4py_gviz, "pm4py_tree.png")
        
        pm4py_infreq_gviz = pt_visualizer.apply(pm4py_infreq_tree)
        pt_visualizer.save(pm4py_infreq_gviz, "pm4py_infreq_tree.png")
        
        # Convert our trees to PM4Py format for visualization
        # This would require a conversion function
        
        print("\nVisualizations saved")
    except Exception as e:
        print(f"Visualization error: {e}")

def test_noise_thresholds():
    """Test the effect of different noise thresholds on the miners."""
    # Create test logs
    pm4py_log, our_log = create_test_log()
    
    print("\n=== Testing Different Noise Thresholds ===")
    for threshold in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        print(f"\nNoise Threshold: {threshold}")
        
        # PM4Py implementation
        pm4py_tree = pm4py.discovery.discover_process_tree_inductive(pm4py_log, noise_threshold=threshold)
        print(f"PM4Py Tree: {pm4py_tree}")
        
        # Our infrequent implementation
        our_infreq_miner = InductiveMiningInfrequent(our_log)
        our_infreq_miner.generate_graph(activity_threshold=0.0, traces_threshold=0.0, noise_threshold=threshold)
        our_infreq_tree = our_infreq_miner.graph.process_tree
        print(f"Our Infrequent Tree: {our_infreq_tree}")
        
        # Our approximate implementation
        our_approx_miner = InductiveMiningApproximate(our_log)
        our_approx_miner.generate_graph(activity_threshold=0.0, traces_threshold=0.0, 
                                      simplification_threshold=threshold, min_bin_freq=threshold)
        our_approx_tree = our_approx_miner.graph.process_tree
        print(f"Our Approximate Tree: {our_approx_tree}")

if __name__ == "__main__":
    compare_inductive_miners()
    test_noise_thresholds() 