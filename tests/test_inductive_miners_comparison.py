import pandas as pd
import pm4py
import os
import networkx as nx
import matplotlib.pyplot as plt
import traceback
from pm4py.objects.log.obj import EventLog
from pm4py.visualization.process_tree import visualizer as pt_visualizer
from pm4py.objects.process_tree.obj import ProcessTree, Operator
from pm4py.objects.process_tree.utils import generic

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

def extract_process_tree(miner):
    """Extract the raw process tree from our miner implementation.
    
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
        # Access the internal process tree
        filtered_log = miner.filtered_log
        # Re-run inductive mining to get the raw process tree structure
        return miner.inductive_mining(filtered_log)
    except Exception as e:
        print(f"Error extracting process tree: {e}")
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

def convert_to_pm4py_tree(our_tree):
    """Convert our process tree format to PM4Py's ProcessTree format.
    
    Parameters
    ----------
    our_tree : tuple
        Our process tree tuple representation
        
    Returns
    -------
    ProcessTree
        PM4Py ProcessTree object
    """
    try:
        if isinstance(our_tree, str):
            # Leaf node - activity
            if our_tree == "tau":
                return ProcessTree(operator=None, label=None)
            else:
                return ProcessTree(operator=None, label=our_tree)
        
        # Operator node
        operator_map = {
            "seq": Operator.SEQUENCE,
            "xor": Operator.XOR,
            "par": Operator.PARALLEL,
            "loop": Operator.LOOP
        }
        
        root = ProcessTree(operator=operator_map[our_tree[0]], label=None)
        
        # Add children
        for child in our_tree[1:]:
            child_tree = convert_to_pm4py_tree(child)
            child_tree.parent = root
            root.children.append(child_tree)
        
        return root
    except Exception as e:
        print(f"Error converting tree: {e}")
        # Return simple tree in case of error
        return ProcessTree(operator=None, label="a")

def compare_trees_simple(pm4py_tree, our_tree_tuple):
    """Simple comparison between PM4Py tree and our tree.
    
    Parameters
    ----------
    pm4py_tree : ProcessTree
        PM4Py ProcessTree object
    our_tree_tuple : tuple
        Our process tree tuple
    
    Returns
    -------
    dict
        Simple comparison results
    """
    try:
        # Get basic information about the PM4Py tree
        pm4py_info = {
            "root_operator": str(pm4py_tree.operator) if pm4py_tree.operator else "LEAF",
            "children_count": len(pm4py_tree.children) if hasattr(pm4py_tree, "children") else 0
        }
        
        # Get basic information about our tree
        our_root_operator = our_tree_tuple[0] if isinstance(our_tree_tuple, tuple) else "LEAF"
        our_children_count = len(our_tree_tuple) - 1 if isinstance(our_tree_tuple, tuple) else 0
        
        our_info = {
            "root_operator": our_root_operator,
            "children_count": our_children_count
        }
        
        # Compare root operators
        operator_match = False
        operator_map = {
            "seq": "SEQUENCE",
            "xor": "XOR",
            "par": "PARALLEL",
            "loop": "LOOP"
        }
        
        if our_root_operator in operator_map:
            operator_match = operator_map[our_root_operator] in str(pm4py_info["root_operator"])
        
        return {
            "pm4py_info": pm4py_info,
            "our_info": our_info,
            "root_operator_match": operator_match,
            "children_count_diff": abs(pm4py_info["children_count"] - our_info["children_count"])
        }
    except Exception as e:
        print(f"Error in simple tree comparison: {e}")
        return {"error": str(e)}

def compare_miners_with_threshold(threshold):
    """Compare miners with a specific threshold."""
    print(f"\n=== Testing with noise threshold: {threshold} ===")
    try:
        pm4py_log, our_log = create_test_log()
        
        # PM4Py implementation
        print("Running PM4Py Inductive Miner...")
        pm4py_tree = pm4py.discovery.discover_process_tree_inductive(pm4py_log, noise_threshold=threshold)
        print(f"PM4Py Tree: {pm4py_tree}")
        
        # Our infrequent implementation
        print("\nRunning our Inductive Miner Infrequent...")
        our_infreq_miner = InductiveMiningInfrequent(our_log)
        our_infreq_miner.generate_graph(activity_threshold=0.0, traces_threshold=0.0, noise_threshold=threshold)
        
        # Extract our raw process tree
        our_tree = extract_process_tree(our_infreq_miner)
        print(f"Our Process Tree: {our_tree}")
        
        # Save visualizations
        try:
            # PM4Py tree visualization
            pm4py_gviz = pt_visualizer.apply(pm4py_tree)
            pm4py_viz_file = f"pm4py_tree_{threshold}.png"
            pt_visualizer.save(pm4py_gviz, pm4py_viz_file)
            print(f"PM4Py visualization saved as {pm4py_viz_file}")
            
            # Our tree visualization
            our_viz_file = f"our_tree_{threshold}.png"
            visualize_our_tree(our_tree, our_viz_file)
            print(f"Our visualization saved as {our_viz_file}")
            
            # Simple structural comparison
            comparison = compare_trees_simple(pm4py_tree, our_tree)
            print("\nStructural Comparison:")
            print(f"- PM4Py root operator: {comparison['pm4py_info']['root_operator']}")
            print(f"- Our root operator: {comparison['our_info']['root_operator']}")
            print(f"- Root operator match: {comparison['root_operator_match']}")
            print(f"- Children count difference: {comparison['children_count_diff']}")
                
        except Exception as e:
            print(f"Comparison error: {e}")
            traceback.print_exc()
    except Exception as e:
        print(f"Error running comparison: {e}")
        traceback.print_exc()

def main():
    # Ensure output directory exists
    os.makedirs("comparison_results", exist_ok=True)
    
    # Test with different noise thresholds
    for threshold in [0.0, 0.2, 0.4]:
        compare_miners_with_threshold(threshold)
    
    print("\n=== Testing Approximate Inductive Miner ===")
    try:
        pm4py_log, our_log = create_test_log()
        
        # PM4Py implementation with highest noise threshold for comparison
        pm4py_tree = pm4py.discovery.discover_process_tree_inductive(pm4py_log, noise_threshold=0.4)
        
        # Our approximate implementation
        our_approx_miner = InductiveMiningApproximate(our_log)
        our_approx_miner.generate_graph(activity_threshold=0.0, traces_threshold=0.0, 
                                      simplification_threshold=0.2, min_bin_freq=0.1)
        
        # Extract our raw process tree
        our_approx_tree = extract_process_tree(our_approx_miner)
        print(f"Our Approximate Tree: {our_approx_tree}")
        
        # Save visualizations
        try:
            # Our tree visualization
            our_viz_file = "our_approx_tree.png"
            visualize_our_tree(our_approx_tree, our_viz_file)
            print(f"Our approximate tree visualization saved as {our_viz_file}")
            
            # Simple structural comparison
            comparison = compare_trees_simple(pm4py_tree, our_approx_tree)
            print("\nStructural Comparison (approximate vs PM4Py 0.4):")
            print(f"- PM4Py root operator: {comparison['pm4py_info']['root_operator']}")
            print(f"- Our root operator: {comparison['our_info']['root_operator']}")
            print(f"- Root operator match: {comparison['root_operator_match']}")
            print(f"- Children count difference: {comparison['children_count_diff']}")
        except Exception as e:
            print(f"Comparison error: {e}")
            traceback.print_exc()
    except Exception as e:
        print(f"Error testing approximate miner: {e}")
        traceback.print_exc()
    
    print("\nTest completed. Check the visualization files and comparison results.")

if __name__ == "__main__":
    main() 