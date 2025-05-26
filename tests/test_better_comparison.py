import pandas as pd
import pm4py
import os
import networkx as nx
import matplotlib.pyplot as plt
import traceback
from pm4py.objects.log.obj import EventLog
from pm4py.visualization.process_tree import visualizer as pt_visualizer

# Import our implementations
from mining_algorithms.inductive_mining import InductiveMining
from mining_algorithms.inductive_mining_infrequent import InductiveMiningInfrequent

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

def extract_process_tree(miner):
    """Extract the raw process tree from our miner implementation without graph visualization.
    
    Parameters
    ----------
    miner : InductiveMining
        The mining algorithm instance
        
    Returns
    -------
    tuple
        The process tree tuple
    """
    try:
        # Access the internal filtered log and run inductive mining directly
        return miner.inductive_mining(miner.filtered_log)
    except Exception as e:
        print(f"Error extracting process tree: {e}")
        traceback.print_exc()
        # Return a simple placeholder tree if extraction fails
        return ("seq", "a", "b", "c", "d")

def visualize_our_tree(tree, filename):
    """Visualize our process tree using NetworkX.
    
    Parameters
    ----------
    tree : tuple
        The process tree tuple
    filename : str
        Output filename for the visualization
    """
    try:
        G = nx.DiGraph()
        node_count = 0
        
        def add_tree_to_graph(tree, parent=None):
            nonlocal node_count
            current_node = node_count
            node_count += 1
            
            if isinstance(tree, str) or isinstance(tree, int):
                # Leaf node (activity or tau)
                label = str(tree)
                G.add_node(current_node, label=label, shape='ellipse')
            else:
                # Operator node
                operator = tree[0]
                G.add_node(current_node, label=operator, shape='box')
                
                # Add children
                for child in tree[1:]:
                    child_node = add_tree_to_graph(child, current_node)
                    G.add_edge(current_node, child_node)
            
            # Connect to parent
            if parent is not None:
                G.add_edge(parent, current_node)
                
            return current_node
        
        add_tree_to_graph(tree)
        
        # Draw the graph
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        node_labels = {node: G.nodes[node]['label'] for node in G.nodes}
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=2000, node_color='lightblue')
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=12)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, arrows=True)
        
        plt.axis('off')
        plt.savefig(filename)
        plt.close()
        
        return filename
    except Exception as e:
        print(f"Error visualizing tree: {e}")
        return None

def compare_trees_operators(pm4py_tree, our_tree_tuple):
    """Compare the operators in PM4Py tree with our tree.
    
    Parameters
    ----------
    pm4py_tree : str
        String representation of PM4Py ProcessTree
    our_tree_tuple : tuple
        Our process tree tuple
    
    Returns
    -------
    dict
        Comparison results
    """
    try:
        # Extract PM4Py operators
        pm4py_operators = []
        for op in ['X(', '->(', '+(',  '*(']:
            pm4py_operators.extend([op for _ in range(str(pm4py_tree).count(op))])
        
        # Get our operators
        our_operators = []
        
        def extract_operators(tree):
            if isinstance(tree, tuple) and len(tree) > 0:
                our_operators.append(tree[0])
                for child in tree[1:]:
                    extract_operators(child)
        
        extract_operators(our_tree_tuple)
        
        # Compare operator counts
        pm4py_op_count = {
            '->': str(pm4py_tree).count('->('),
            'X': str(pm4py_tree).count('X('),
            '+': str(pm4py_tree).count('+('),
            '*': str(pm4py_tree).count('*(')
        }
        
        our_op_count = {
            '->': our_operators.count('->'),
            'X': our_operators.count('X'),
            '+': our_operators.count('+'),
            '*': our_operators.count('*')
        }
        
        # Calculate similarity
        similarity = sum(min(pm4py_op_count[op], our_op_count[op]) for op in pm4py_op_count) / \
                    max(1, sum(max(pm4py_op_count[op], our_op_count[op]) for op in pm4py_op_count))
        
        return {
            'pm4py_operators': pm4py_op_count,
            'our_operators': our_op_count,
            'operator_similarity': similarity
        }
    except Exception as e:
        print(f"Error comparing operators: {e}")
        return {'error': str(e)}

def test_with_noise_threshold(threshold):
    """Test our inductive miner implementation with a specific noise threshold.
    
    Parameters
    ----------
    threshold : float
        Noise threshold for filtering
    
    Returns
    -------
    dict
        Test results
    """
    print(f"\n=== Testing improved implementation with noise threshold: {threshold} ===")
    
    try:
        # Create test log
        pm4py_log, our_log = create_test_log()
        
        # Run PM4Py implementation
        print("Running PM4Py Inductive Miner...")
        pm4py_tree = pm4py.discovery.discover_process_tree_inductive(pm4py_log, noise_threshold=threshold)
        print(f"PM4Py Tree: {pm4py_tree}")
        
        # Run our improved implementation
        print("\nRunning our improved Inductive Miner Infrequent...")
        our_infreq_miner = InductiveMiningInfrequent(our_log)
        
        # Apply filtering but don't generate graph
        our_infreq_miner.activity_threshold = 0.0
        our_infreq_miner.traces_threshold = 0.0
        our_infreq_miner.noise_threshold = threshold
        
        # Filter the log manually
        events_to_remove = our_infreq_miner.get_events_to_remove(our_infreq_miner.activity_threshold)
        min_traces_frequency = our_infreq_miner.calulate_minimum_traces_frequency(our_infreq_miner.traces_threshold)
        
        from logs.filters import filter_events, filter_traces
        filtered_log = filter_traces(our_log, min_traces_frequency)
        filtered_log = filter_events(filtered_log, events_to_remove)
        our_infreq_miner.filtered_log = filtered_log
        
        # Extract our process tree directly without graph generation
        our_tree = extract_process_tree(our_infreq_miner)
        print(f"Our Process Tree: {our_tree}")
        
        # Save visualizations
        out_dir = "improved_comparison"
        os.makedirs(out_dir, exist_ok=True)
        
        pm4py_viz_file = f"{out_dir}/pm4py_tree_{threshold}.png"
        our_viz_file = f"{out_dir}/our_tree_{threshold}.png"
        
        # PM4Py visualization
        pm4py_gviz = pt_visualizer.apply(pm4py_tree)
        pt_visualizer.save(pm4py_gviz, pm4py_viz_file)
        print(f"PM4Py visualization saved as {pm4py_viz_file}")
        
        # Our visualization
        visualize_our_tree(our_tree, our_viz_file)
        print(f"Our visualization saved as {our_viz_file}")
        
        # Compare operators
        comparison = compare_trees_operators(pm4py_tree, our_tree)
        print("\nOperator Comparison:")
        print(f"PM4Py operators: {comparison['pm4py_operators']}")
        print(f"Our operators: {comparison['our_operators']}")
        print(f"Operator similarity: {comparison['operator_similarity'] * 100:.1f}%")
        
        return {
            'threshold': threshold,
            'pm4py_tree': pm4py_tree,
            'our_tree': our_tree,
            'comparison': comparison
        }
    except Exception as e:
        print(f"Error in test: {e}")
        traceback.print_exc()
        return {'error': str(e)}

def create_summary_visualization(results):
    """Create a summary visualization comparing results across different thresholds.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping thresholds to results
    """
    try:
        # Create a summary visualization
        plt.figure(figsize=(10, 6))
        
        thresholds = []
        similarities = []
        
        for threshold, result in results.items():
            if 'comparison' in result:
                thresholds.append(threshold)
                similarities.append(result['comparison']['operator_similarity'] * 100)
        
        plt.bar(thresholds, similarities, color='steelblue')
        plt.axhline(y=80, color='r', linestyle='--', label='Good similarity (80%)')
        plt.ylim(0, 105)
        
        # Add percentage labels on bars
        for i, v in enumerate(similarities):
            plt.text(i, v + 3, f"{v:.1f}%", ha='center')
        
        plt.xlabel('Noise Threshold')
        plt.ylabel('Operator Similarity (%)')
        plt.title('Process Tree Similarity: PM4Py vs Our Implementation')
        plt.xticks(thresholds)
        plt.legend()
        
        # Save the figure
        out_dir = "improved_comparison"
        os.makedirs(out_dir, exist_ok=True)
        plt.savefig(f"{out_dir}/similarity_comparison.png")
        plt.close()
        
        print(f"\nSummary visualization saved as {out_dir}/similarity_comparison.png")
        
        # Create a side-by-side image of all process trees
        fig, axes = plt.subplots(len(thresholds), 2, figsize=(15, 5 * len(thresholds)))
        
        for i, threshold in enumerate(sorted(thresholds)):
            # Load PM4Py image
            pm4py_img = plt.imread(f"{out_dir}/pm4py_tree_{threshold}.png")
            axes[i, 0].imshow(pm4py_img)
            axes[i, 0].set_title(f"PM4Py Tree (threshold={threshold})")
            axes[i, 0].axis('off')
            
            # Load our image
            our_img = plt.imread(f"{out_dir}/our_tree_{threshold}.png")
            axes[i, 1].imshow(our_img)
            axes[i, 1].set_title(f"Our Implementation (threshold={threshold})")
            axes[i, 1].axis('off')
        
        plt.tight_layout()
        plt.savefig(f"{out_dir}/tree_comparison.png")
        plt.close()
        
        print(f"Side-by-side comparison saved as {out_dir}/tree_comparison.png")
        
    except Exception as e:
        print(f"Error creating summary visualization: {e}")
        traceback.print_exc()

def main():
    """Run tests with different noise thresholds."""
    results = {}
    
    for threshold in [0.0, 0.2, 0.4]:
        results[threshold] = test_with_noise_threshold(threshold)
    
    # Summarize results
    print("\n=== Summary of Results ===")
    for threshold, result in results.items():
        if 'comparison' in result:
            similarity = result['comparison']['operator_similarity'] * 100
            print(f"Threshold {threshold}: Operator similarity: {similarity:.1f}%")
    
    # Create summary visualizations
    create_summary_visualization(results)
    
    print("\nTest completed. Check the visualization files in the 'improved_comparison' directory.")

if __name__ == "__main__":
    main() 