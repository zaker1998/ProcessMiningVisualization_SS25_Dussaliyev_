import pm4py
import pandas as pd
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.visualization.process_tree import visualizer as pt_visualizer
import os

# Test with a small log
log = [
    ['a', 'b', 'c', 'd'],
    ['a', 'c', 'b', 'd'],
    ['a', 'b', 'c', 'd'],
    ['a', 'c', 'd'],
    ['a', 'b', 'd']
]

# Convert to the format PM4Py expects
event_log = []
for trace_idx, trace in enumerate(log):
    events = []
    for event_idx, activity in enumerate(trace):
        events.append({
            'concept:name': activity,
            'time:timestamp': pd.Timestamp(2023, 1, 1, hour=event_idx),
            'case:concept:name': f'case_{trace_idx}'
        })
    event_log.append(events)

log_obj = pm4py.objects.log.obj.EventLog(event_log)

# Run the different inductive miner variants
print("=== Standard Inductive Miner ===")
tree1 = pm4py.discovery.discover_process_tree_inductive(log_obj)
print(f"Process Tree: {tree1}")

print("\n=== Inductive Miner Infrequent (noise_threshold=0.2) ===")
tree2 = pm4py.discovery.discover_process_tree_inductive(log_obj, noise_threshold=0.2)
print(f"Process Tree: {tree2}")

# Get the variant with DFG input
print("\n=== Using DFG as input ===")
dfg, start_activities, end_activities = pm4py.discovery.discover_directly_follows_graph(log_obj)
print(f"DFG: {dfg}")
print(f"Start activities: {start_activities}")
print(f"End activities: {end_activities}")

# Testing noise thresholds
print("\n=== Testing with different noise thresholds ===")
for threshold in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
    tree = pm4py.discovery.discover_process_tree_inductive(log_obj, noise_threshold=threshold)
    print(f"Noise Threshold: {threshold}, Process Tree: {tree}")

# Visualize trees (if graphviz is installed)
try:
    gviz1 = pt_visualizer.apply(tree1)
    pt_visualizer.save(gviz1, "standard_inductive.png")
    
    gviz2 = pt_visualizer.apply(tree2)
    pt_visualizer.save(gviz2, "infrequent_inductive.png")
    
    print("\nVisualization files created!")
except Exception as e:
    print(f"Visualization error: {e}")

# Convert to Petri net
print("\n=== Converting to Petri Net ===")
net, initial_marking, final_marking = pm4py.convert_to_petri_net(tree1)
print("Converted to Petri net successfully.")

# Visualize Petri net
try:
    from pm4py.visualization.petri_net import visualizer as pn_visualizer
    gviz = pn_visualizer.apply(net, initial_marking, final_marking)
    pn_visualizer.save(gviz, "petri_net.png")
    print("Petri net visualization created.")
except Exception as e:
    print(f"Petri net visualization error: {e}") 