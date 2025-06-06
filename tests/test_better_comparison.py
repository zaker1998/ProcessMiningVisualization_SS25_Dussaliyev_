import pandas as pd
import pm4py
import traceback
from pm4py.objects.log.obj import EventLog

def create_test_log():
    """Create a test log for comparing the algorithms."""
    # Define some test traces with specific patterns to test algorithm behavior
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
    
    return EventLog(event_log_pm4py)

def test_pm4py_inductive_miners():
    """Test PM4Py's inductive miner implementations with different thresholds."""
    print("\n=== Testing PM4Py Inductive Miners ===")
    
    try:
        # Create test log
        log = create_test_log()
        
        # Test with different thresholds
        thresholds = [0.0, 0.2, 0.4, 0.6, 0.8]
        
        print("\n--- Results of Standard Inductive Miner with Different Noise Thresholds ---")
        print(f"| {'Threshold':^10} | {'Process Tree':^60} |")
        print(f"| {'-'*10:^10} | {'-'*60:^60} |")
        
        for threshold in thresholds:
            # Run PM4Py implementation
            tree = pm4py.discovery.discover_process_tree_inductive(log, noise_threshold=threshold)
            
            # Format the tree string to fit in the table
            tree_str = str(tree)
            if len(tree_str) > 57:
                tree_str = tree_str[:54] + "..."
                
            print(f"| {threshold:^10.1f} | {tree_str:<60} |")
        
        # Compare structure types with different noise thresholds
        print("\n--- Comparing Operator Counts at Different Thresholds ---")
        print(f"| {'Threshold':^10} | {'Sequence (->)':^12} | {'XOR (×)':^10} | {'Parallel (+)':^12} | {'Loop (*)':^10} |")
        print(f"| {'-'*10:^10} | {'-'*12:^12} | {'-'*10:^10} | {'-'*12:^12} | {'-'*10:^10} |")
        
        for threshold in thresholds:
            tree = pm4py.discovery.discover_process_tree_inductive(log, noise_threshold=threshold)
            tree_str = str(tree)
            
            # Count operators
            seq_count = tree_str.count('->(')
            xor_count = tree_str.count('X(')
            par_count = tree_str.count('+(')
            loop_count = tree_str.count('*(')
            
            print(f"| {threshold:^10.1f} | {seq_count:^12d} | {xor_count:^10d} | {par_count:^12d} | {loop_count:^10d} |")
        
        # Analyze structure changes
        print("\n--- Analysis of Tree Structure Changes ---")
        print("As the noise threshold increases:")
        
        # Run detailed comparison between thresholds
        prev_tree = None
        prev_threshold = None
        
        for threshold in thresholds:
            tree = pm4py.discovery.discover_process_tree_inductive(log, noise_threshold=threshold)
            
            if prev_tree is not None:
                # Compare tree structures
                if str(tree) != str(prev_tree):
                    print(f"• Change detected between threshold {prev_threshold} and {threshold}")
                    
                    # Compare operator counts
                    curr_seq = str(tree).count('->(')
                    curr_xor = str(tree).count('X(')
                    curr_par = str(tree).count('+(')
                    curr_loop = str(tree).count('*(')
                    
                    prev_seq = str(prev_tree).count('->(')
                    prev_xor = str(prev_tree).count('X(')
                    prev_par = str(prev_tree).count('+(')
                    prev_loop = str(prev_tree).count('*(')
                    
                    # Report significant changes
                    if curr_seq != prev_seq:
                        print(f"  - Sequence operators: {prev_seq} → {curr_seq}")
                    if curr_xor != prev_xor:
                        print(f"  - XOR operators: {prev_xor} → {curr_xor}")
                    if curr_par != prev_par:
                        print(f"  - Parallel operators: {prev_par} → {curr_par}")
                    if curr_loop != prev_loop:
                        print(f"  - Loop operators: {prev_loop} → {curr_loop}")
            
            prev_tree = tree
            prev_threshold = threshold
            
        # Summary
        print("\n--- Summary ---")
        print("For implementing an inductive miner comparable to PM4Py:")
        print("1. The noise threshold parameter significantly affects tree structure")
        print("2. Higher thresholds tend to simplify the model by filtering infrequent behavior")
        print("3. The standard implementation (0.0 threshold) captures all behavior in the log")
        print("4. A threshold around 0.2-0.4 provides a good balance for most logs")
        
        return True
    except Exception as e:
        print(f"Error in PM4Py test: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pm4py_inductive_miners() 