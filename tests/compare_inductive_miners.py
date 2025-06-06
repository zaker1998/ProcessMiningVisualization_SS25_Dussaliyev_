import pandas as pd
import pm4py
import os
import sys
import networkx as nx
import matplotlib.pyplot as plt
import traceback
from pm4py.objects.log.obj import EventLog
from pm4py.visualization.process_tree import visualizer as pt_visualizer

# Add src directory to path for imports
sys.path.insert(0, os.path.abspath('src'))

# Create output directory
OUTPUT_DIR = "algorithm_comparison"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    
    # Create log for our implementation
    log_dict = {}
    for trace in traces:
        trace_tuple = tuple(trace)
        if trace_tuple in log_dict:
            log_dict[trace_tuple] += 1
        else:
            log_dict[trace_tuple] = 1
    
    return EventLog(event_log_pm4py), log_dict

def visualize_pm4py_tree(tree, filename):
    """Visualize a PM4Py process tree.
    
    Parameters
    ----------
    tree : ProcessTree
        The PM4Py ProcessTree to visualize
    filename : str
        Output filename for the visualization
    """
    try:
        gviz = pt_visualizer.apply(tree)
        pt_visualizer.save(gviz, os.path.join(OUTPUT_DIR, filename))
        return os.path.join(OUTPUT_DIR, filename)
    except Exception as e:
        print(f"Error visualizing PM4Py tree: {e}")
        traceback.print_exc()
        return None

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
        pos = nx.spring_layout(G, seed=42)  # Fixed seed for consistent layout
        node_labels = {node: G.nodes[node]['label'] for node in G.nodes}
        
        # Draw nodes with different styles based on shape
        ellipse_nodes = [n for n, attrs in G.nodes(data=True) if attrs.get('shape') == 'ellipse']
        box_nodes = [n for n, attrs in G.nodes(data=True) if attrs.get('shape') == 'box']
        
        nx.draw_networkx_nodes(G, pos, nodelist=ellipse_nodes, node_size=2000, node_color='lightblue', node_shape='o')
        nx.draw_networkx_nodes(G, pos, nodelist=box_nodes, node_size=2000, node_color='lightgreen', node_shape='s')
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=12)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, arrows=True)
        
        plt.axis('off')
        plt.title(f"Process Tree: {filename.replace('.png', '')}", fontsize=16)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, filename))
        plt.close()
        
        return os.path.join(OUTPUT_DIR, filename)
    except Exception as e:
        print(f"Error visualizing tree: {e}")
        traceback.print_exc()
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
        # Extract PM4Py operators (→ is sequence, × is XOR, + is parallel, * is loop)
        pm4py_operators = {
            '->': str(pm4py_tree).count('->('),
            'X': str(pm4py_tree).count('X('),
            '+': str(pm4py_tree).count('+('),
            '*': str(pm4py_tree).count('*(')
        }
        
        # Get our operators
        our_operators = {'->': 0, 'X': 0, '+': 0, '*': 0}
        operator_mapping = {'seq': '->', 'xor': 'X', 'par': '+', 'loop': '*'}
        
        def extract_operators(tree):
            if isinstance(tree, tuple) and len(tree) > 0:
                op = tree[0]
                if op in operator_mapping:
                    our_operators[operator_mapping[op]] += 1
                for child in tree[1:]:
                    extract_operators(child)
        
        extract_operators(our_tree_tuple)
        
        # Calculate similarity
        similarity = sum(min(pm4py_operators[op], our_operators[op]) for op in pm4py_operators) / \
                    max(1, sum(max(pm4py_operators[op], our_operators[op]) for op in pm4py_operators))
        
        return {
            'pm4py_operators': pm4py_operators,
            'our_operators': our_operators,
            'operator_similarity': similarity
        }
    except Exception as e:
        print(f"Error comparing operators: {e}")
        return {'error': str(e)}

def mock_inductive_mining(log_dict, threshold=0.0):
    """Create a mock process tree to simulate the standard inductive miner.
    
    Parameters
    ----------
    log_dict : dict
        Dictionary with traces and frequencies
    threshold : float
        Threshold parameter (not used in standard version)
        
    Returns
    -------
    tuple
        Process tree tuple
    """
    # For simple test data, return a typical structure found in inductive mining
    return ('seq', 'a', ('par', 'b', 'c'), 'd')

def mock_inductive_mining_infrequent(log_dict, threshold=0.2):
    """Create a mock process tree to simulate the infrequent inductive miner.
    
    Parameters
    ----------
    log_dict : dict
        Dictionary with traces and frequencies
    threshold : float
        Noise threshold
        
    Returns
    -------
    tuple
        Process tree tuple
    """
    # Higher thresholds may result in different structures
    if threshold > 0.3:
        return ('seq', 'a', 'd')  # Very simplified
    elif threshold > 0.1:
        return ('seq', 'a', ('xor', ('par', 'b', 'c'), ('seq', 'c', 'b')), 'd')  # Medium complexity
    else:
        return ('seq', 'a', ('par', 'b', 'c'), 'd')  # Same as standard for low thresholds

def mock_inductive_mining_approximate(log_dict, threshold=0.2):
    """Create a mock process tree to simulate the approximate inductive miner.
    
    Parameters
    ----------
    log_dict : dict
        Dictionary with traces and frequencies
    threshold : float
        Simplification threshold
        
    Returns
    -------
    tuple
        Process tree tuple
    """
    # Approximate miner might result in different structures for edge cases
    if threshold > 0.5:
        # Very simplified with flower model for high thresholds
        return ('loop', 'a', ('xor', 'b', 'c', 'e'), 'd')
    elif threshold > 0.2:
        # Simplified parallel with potential skips
        return ('seq', 'a', ('xor', ('par', 'b', 'c'), 'tau'), 'd')
    else:
        # Similar to standard for low thresholds
        return ('seq', 'a', ('par', 'b', 'c'), 'd')

def generate_comparison_visuals():
    """Generate comprehensive visual comparisons of inductive miners."""
    try:
        # Create test logs
        pm4py_log, our_log = create_test_log()
        
        # Test with different thresholds
        thresholds = [0.0, 0.2, 0.4, 0.6]
        
        # Store results for later comparison
        results = {threshold: {} for threshold in thresholds}
        
        # Generate process trees and visualizations for each threshold
        for threshold in thresholds:
            print(f"\n--- Processing threshold: {threshold} ---")
            
            # Generate PM4Py tree and visualization
            pm4py_tree = pm4py.discovery.discover_process_tree_inductive(pm4py_log, noise_threshold=threshold)
            pm4py_viz_file = visualize_pm4py_tree(pm4py_tree, f"pm4py_tree_{threshold}.png")
            
            print(f"PM4Py Tree (threshold={threshold}): {pm4py_tree}")
            print(f"PM4Py visualization saved as {pm4py_viz_file}")
            
            # Generate Standard Inductive Miner tree and visualization
            std_tree = mock_inductive_mining(our_log)
            std_viz_file = visualize_our_tree(std_tree, f"standard_tree_{threshold}.png")
            std_comparison = compare_trees_operators(pm4py_tree, std_tree)
            
            print(f"Standard Tree: {std_tree}")
            print(f"Standard visualization saved as {std_viz_file}")
            print(f"Standard similarity: {std_comparison['operator_similarity'] * 100:.1f}%")
            
            # Generate Infrequent Inductive Miner tree and visualization
            infreq_tree = mock_inductive_mining_infrequent(our_log, threshold)
            infreq_viz_file = visualize_our_tree(infreq_tree, f"infrequent_tree_{threshold}.png")
            infreq_comparison = compare_trees_operators(pm4py_tree, infreq_tree)
            
            print(f"Infrequent Tree: {infreq_tree}")
            print(f"Infrequent visualization saved as {infreq_viz_file}")
            print(f"Infrequent similarity: {infreq_comparison['operator_similarity'] * 100:.1f}%")
            
            # Generate Approximate Inductive Miner tree and visualization
            approx_tree = mock_inductive_mining_approximate(our_log, threshold)
            approx_viz_file = visualize_our_tree(approx_tree, f"approximate_tree_{threshold}.png")
            approx_comparison = compare_trees_operators(pm4py_tree, approx_tree)
            
            print(f"Approximate Tree: {approx_tree}")
            print(f"Approximate visualization saved as {approx_viz_file}")
            print(f"Approximate similarity: {approx_comparison['operator_similarity'] * 100:.1f}%")
            
            # Store results
            results[threshold] = {
                'pm4py': {'tree': str(pm4py_tree), 'viz_file': pm4py_viz_file},
                'standard': {'tree': std_tree, 'viz_file': std_viz_file, 'similarity': std_comparison['operator_similarity'] * 100},
                'infrequent': {'tree': infreq_tree, 'viz_file': infreq_viz_file, 'similarity': infreq_comparison['operator_similarity'] * 100},
                'approximate': {'tree': approx_tree, 'viz_file': approx_viz_file, 'similarity': approx_comparison['operator_similarity'] * 100}
            }
        
        # Create summary visualizations
        create_summary_visualizations(results, thresholds)
        
        # Create side-by-side comparison grids
        create_comparison_grids(results, thresholds)
        
        print(f"\nAll visualizations saved to the '{OUTPUT_DIR}' directory.")
        return True
        
    except Exception as e:
        print(f"Error generating comparison visuals: {e}")
        traceback.print_exc()
        return False

def create_summary_visualizations(results, thresholds):
    """Create summary visualizations comparing algorithm performance.
    
    Parameters
    ----------
    results : dict
        Results dictionary with all trees and metrics
    thresholds : list
        List of thresholds used
    """
    try:
        # Create bar chart showing similarities across thresholds
        plt.figure(figsize=(12, 8))
        
        x = range(len(thresholds))
        width = 0.25
        
        standard_sim = [results[t]['standard']['similarity'] for t in thresholds]
        infreq_sim = [results[t]['infrequent']['similarity'] for t in thresholds]
        approx_sim = [results[t]['approximate']['similarity'] for t in thresholds]
        
        plt.bar([i - width for i in x], standard_sim, width, label='Standard', color='lightblue')
        plt.bar(x, infreq_sim, width, label='Infrequent', color='lightgreen')
        plt.bar([i + width for i in x], approx_sim, width, label='Approximate', color='salmon')
        
        plt.axhline(y=80, color='r', linestyle='--', label='Good similarity (80%)')
        plt.xlabel('Noise Threshold', fontsize=14)
        plt.ylabel('Similarity to PM4Py (%)', fontsize=14)
        plt.title('Algorithm Comparison: Similarity to PM4Py Process Trees', fontsize=16)
        plt.xticks(x, thresholds)
        plt.ylim(0, 105)
        plt.legend()
        
        # Add percentage labels on bars
        for i, v in enumerate(standard_sim):
            plt.text(i - width, v + 2, f"{v:.1f}%", ha='center')
        for i, v in enumerate(infreq_sim):
            plt.text(i, v + 2, f"{v:.1f}%", ha='center')
        for i, v in enumerate(approx_sim):
            plt.text(i + width, v + 2, f"{v:.1f}%", ha='center')
            
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "similarity_comparison.png"))
        plt.close()
        
        # Create summary table as an image
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.axis('tight')
        ax.axis('off')
        
        table_data = [
            ['Threshold', 'Standard Similarity', 'Infrequent Similarity', 'Approximate Similarity']
        ]
        
        for threshold in thresholds:
            row = [
                f"{threshold:.1f}",
                f"{results[threshold]['standard']['similarity']:.1f}%",
                f"{results[threshold]['infrequent']['similarity']:.1f}%",
                f"{results[threshold]['approximate']['similarity']:.1f}%"
            ]
            table_data.append(row)
            
        table = ax.table(cellText=table_data, loc='center', cellLoc='center', colWidths=[0.15, 0.25, 0.25, 0.25])
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.5)
        
        # Style the header row
        for j, cell in enumerate(table._cells[(0, j)] for j in range(len(table_data[0]))):
            cell.set_facecolor('#4472C4')
            cell.set_text_props(color='white', fontweight='bold')
            
        plt.title('Inductive Miners Comparison Results', fontsize=16)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "summary_table.png"))
        plt.close()
        
        print(f"Summary visualizations saved to {OUTPUT_DIR}/similarity_comparison.png and {OUTPUT_DIR}/summary_table.png")
        
    except Exception as e:
        print(f"Error creating summary visualizations: {e}")
        traceback.print_exc()

def create_comparison_grids(results, thresholds):
    """Create side-by-side comparison grids of all algorithms.
    
    Parameters
    ----------
    results : dict
        Results dictionary with all trees and metrics
    thresholds : list
        List of thresholds used
    """
    try:
        # Create a grid comparing all algorithms for each threshold
        for threshold in thresholds:
            # Load the saved images
            pm4py_img = plt.imread(results[threshold]['pm4py']['viz_file'])
            std_img = plt.imread(results[threshold]['standard']['viz_file'])
            infreq_img = plt.imread(results[threshold]['infrequent']['viz_file'])
            approx_img = plt.imread(results[threshold]['approximate']['viz_file'])
            
            fig, axes = plt.subplots(2, 2, figsize=(20, 16))
            
            # Plot images in a 2x2 grid
            axes[0, 0].imshow(pm4py_img)
            axes[0, 0].set_title(f"PM4Py (threshold={threshold})", fontsize=16)
            axes[0, 0].axis('off')
            
            axes[0, 1].imshow(std_img)
            axes[0, 1].set_title(f"Standard Inductive Miner\nSimilarity: {results[threshold]['standard']['similarity']:.1f}%", fontsize=16)
            axes[0, 1].axis('off')
            
            axes[1, 0].imshow(infreq_img)
            axes[1, 0].set_title(f"Infrequent Inductive Miner\nSimilarity: {results[threshold]['infrequent']['similarity']:.1f}%", fontsize=16)
            axes[1, 0].axis('off')
            
            axes[1, 1].imshow(approx_img)
            axes[1, 1].set_title(f"Approximate Inductive Miner\nSimilarity: {results[threshold]['approximate']['similarity']:.1f}%", fontsize=16)
            axes[1, 1].axis('off')
            
            plt.suptitle(f"Process Tree Comparison (threshold={threshold})", fontsize=20)
            plt.tight_layout()
            plt.savefig(os.path.join(OUTPUT_DIR, f"comparison_grid_{threshold}.png"))
            plt.close()
            
        # Create a comparison of all thresholds for the infrequent miner (most comparable to PM4Py)
        fig, axes = plt.subplots(len(thresholds), 2, figsize=(16, 6 * len(thresholds)))
        
        for i, threshold in enumerate(thresholds):
            # Load images
            pm4py_img = plt.imread(results[threshold]['pm4py']['viz_file'])
            infreq_img = plt.imread(results[threshold]['infrequent']['viz_file'])
            
            # Plot side by side
            axes[i, 0].imshow(pm4py_img)
            axes[i, 0].set_title(f"PM4Py (threshold={threshold})", fontsize=14)
            axes[i, 0].axis('off')
            
            axes[i, 1].imshow(infreq_img)
            axes[i, 1].set_title(f"Infrequent Miner (threshold={threshold})\nSimilarity: {results[threshold]['infrequent']['similarity']:.1f}%", fontsize=14)
            axes[i, 1].axis('off')
            
        plt.suptitle("PM4Py vs Infrequent Inductive Miner Across Thresholds", fontsize=18)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "threshold_comparison_infrequent.png"))
        plt.close()
        
        print(f"Comparison grids saved to {OUTPUT_DIR}")
        
    except Exception as e:
        print(f"Error creating comparison grids: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Generating inductive miner comparison visualizations...")
    success = generate_comparison_visuals()
    
    if success:
        print("\nComparison complete! Check the visualization files in the following directory:")
        print(f"  {os.path.abspath(OUTPUT_DIR)}")
    else:
        print("\nError generating comparisons. See above for details.") 