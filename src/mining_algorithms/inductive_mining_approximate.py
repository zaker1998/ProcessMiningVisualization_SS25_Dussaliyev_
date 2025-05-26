from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, parallel_cut, sequence_cut, loop_cut
import numpy as np
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split


class InductiveMiningApproximate(InductiveMining):
    """
    A class to generate a graph from a log using the Approximate Inductive Miner algorithm.
    This variant uses more aggressive cut detection and pruning strategies to simplify the process tree.
    """

    def __init__(self, log):
        super().__init__(log)
        self.simplification_threshold = 0.1  # Default simplification threshold
        self.min_bin_freq = 0.2  # Default minimum bin frequency for activity binning
        self.max_recursion_depth = 10  # Limit recursion to avoid overly complex models
        self.current_depth = 0  # Track current recursion depth
        
    def generate_graph(self, activity_threshold=0.0, traces_threshold=0.2, 
                       simplification_threshold=0.1, min_bin_freq=0.2, max_recursion_depth=10):
        """Generate a graph using the Approximate Inductive Miner algorithm.

        Parameters
        ----------
        activity_threshold : float
            The activity threshold for filtering of the log.
        traces_threshold : float
            The traces threshold for filtering of the log.
        simplification_threshold : float
            Threshold for simplifying directly-follows relations.
            Relations with a frequency lower than threshold * max_relation_frequency will be ignored.
        min_bin_freq : float
            Minimum frequency for binning activities with similar behavior.
        max_recursion_depth : int
            Maximum recursion depth to prevent overly complex models.
        """
        self.simplification_threshold = simplification_threshold
        self.min_bin_freq = min_bin_freq
        self.max_recursion_depth = max_recursion_depth
        self.current_depth = 0
        super().generate_graph(activity_threshold, traces_threshold)
    
    def inductive_mining(self, log):
        """Generate a process tree from the log using the Approximate Inductive Mining algorithm.
        This overrides the standard inductive mining method to include additional approximation strategies.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.

        Returns
        -------
        tuple
            A tuple representing the process tree.
        """
        # Increment recursion depth
        self.current_depth += 1
        
        # Check if we hit the recursion limit
        if self.current_depth > self.max_recursion_depth:
            # Get the most frequent activities in the log
            activities = self.get_log_alphabet(log)
            if len(activities) > 1:
                return ("par", *activities)  # Use parallel construct as approximation
            elif len(activities) == 1:
                return list(activities)[0]
            else:
                return "tau"
        
        # Check for base cases
        if tree := self.base_cases(log):
            self.current_depth -= 1
            return tree
            
        # For small logs with many variants, apply activity clustering
        if len(log) < 10 and len(self.get_log_alphabet(log)) > 5:
            clustered_log = self.bin_similar_activities(log)
            if len(clustered_log) < len(log):
                result = self.inductive_mining(clustered_log)
                self.current_depth -= 1
                return result
        
        # Try standard cut detection with simplification
        if tuple() not in log:
            if partitions := self.calulate_approximate_cut(log):
                # Recursive call with partitions
                operation = partitions[0]
                result = (operation, *list(map(self.inductive_mining, partitions[1:])))
                self.current_depth -= 1
                return result
        
        # Fallthrough mechanisms
        result = self.approximate_fallthrough(log)
        self.current_depth -= 1
        return result
        
    def calulate_approximate_cut(self, log):
        """Find a partitioning of the log using the different cut methods with approximations.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.

        Returns
        -------
        tuple | None
            A process tree representing the partitioning of the log if a cut was found, otherwise None.
        """
        # Create DFG from log
        dfg = DFG(log)
        
        # Filter infrequent directly-follows relations for approximation
        filtered_dfg = self.filter_infrequent_relations(dfg)
        
        # Try the different cuts
        if partitions := exclusive_cut(filtered_dfg):
            return ("xor", *exclusive_split(log, partitions))
        elif partitions := sequence_cut(filtered_dfg):
            return ("seq", *sequence_split(log, partitions))
        elif partitions := parallel_cut(filtered_dfg):
            return ("par", *parallel_split(log, partitions))
        elif partitions := loop_cut(filtered_dfg):
            return ("loop", *loop_split(log, partitions))
            
        # If no cuts found with filtering, try aggressive filtering
        aggressive_dfg = self.aggressive_filter_relations(filtered_dfg)
        
        if partitions := exclusive_cut(aggressive_dfg):
            return ("xor", *exclusive_split(log, partitions))
        elif partitions := sequence_cut(aggressive_dfg):
            return ("seq", *sequence_split(log, partitions))
        elif partitions := parallel_cut(aggressive_dfg):
            return ("par", *parallel_split(log, partitions))
        elif partitions := loop_cut(aggressive_dfg):
            return ("loop", *loop_split(log, partitions))

        return None
    
    def filter_infrequent_relations(self, dfg):
        """Filter infrequent directly-follows relations.
        
        Parameters
        ----------
        dfg : DFG
            The directly-follows graph.
            
        Returns
        -------
        DFG
            A new DFG with infrequent relations filtered out.
        """
        # Create a new DFG
        filtered_dfg = DFG()
        
        # Copy nodes
        for node in dfg.get_nodes():
            filtered_dfg.add_node(node)
        
        # Copy start and end nodes
        filtered_dfg.start_nodes = dfg.start_nodes.copy()
        filtered_dfg.end_nodes = dfg.end_nodes.copy()
        
        # Get all edges and their frequencies
        edges = dfg.get_edges()
        edge_frequencies = self.calculate_edge_frequencies(edges)
        
        # Find max frequency
        max_frequency = max(edge_frequencies.values(), default=1)
        threshold = max_frequency * self.simplification_threshold
        
        # Add edges that pass the threshold
        for (source, target), frequency in edge_frequencies.items():
            if frequency >= threshold:
                filtered_dfg.add_edge(source, target)
                
        return filtered_dfg
    
    def calculate_edge_frequencies(self, edges):
        """Calculate frequencies for edges based on the log.
        
        Parameters
        ----------
        edges : set[tuple[str, str]]
            Set of edges in the DFG
            
        Returns
        -------
        dict
            Dictionary mapping edges to frequencies
        """
        edge_frequencies = {edge: 0 for edge in edges}
        
        for trace, frequency in self.log.items():
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                if edge in edge_frequencies:
                    edge_frequencies[edge] += frequency
        
        return edge_frequencies
        
    def aggressive_filter_relations(self, dfg):
        """More aggressive filtering of directly-follows relations.
        
        Parameters
        ----------
        dfg : DFG
            The directly-follows graph.
            
        Returns
        -------
        DFG
            A new DFG with aggressively filtered relations.
        """
        # Create a new DFG
        filtered_dfg = DFG()
        
        # Copy nodes
        for node in dfg.get_nodes():
            filtered_dfg.add_node(node)
        
        # Copy start and end nodes
        filtered_dfg.start_nodes = dfg.start_nodes.copy()
        filtered_dfg.end_nodes = dfg.end_nodes.copy()
        
        # Get all edges
        edges = dfg.get_edges()
        
        # Check if there are any edges
        if not edges:
            return filtered_dfg
        
        # Calculate frequencies
        edge_frequencies = self.calculate_edge_frequencies(edges)
        
        # Get average frequency
        frequencies = list(edge_frequencies.values())
        avg_frequency = sum(frequencies) / len(frequencies)
        
        # Add edges above average frequency
        for (source, target), frequency in edge_frequencies.items():
            if frequency >= avg_frequency:
                filtered_dfg.add_edge(source, target)
                
        return filtered_dfg
    
    def bin_similar_activities(self, log):
        """Bin activities with similar behavior to simplify the log.
        
        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies.
            
        Returns
        -------
        dict
            A new log with activities binned/clustered.
        """
        # Get activities and their frequencies
        activities = list(self.get_log_alphabet(log))
        if len(activities) <= 1:
            return log
            
        # Create DFG for behavior analysis
        dfg = DFG(log)
        
        # Create behavior profile for each activity based on incoming/outgoing edges
        behavior_profiles = {}
        for activity in activities:
            incoming = dfg.get_predecessors(activity)
            outgoing = dfg.get_successors(activity)
            behavior_profiles[activity] = (frozenset(incoming), frozenset(outgoing))
        
        # Group activities with similar behavior
        similarity_groups = {}
        for act1 in activities:
            for act2 in activities:
                if act1 >= act2:  # Skip duplicates and self-comparisons
                    continue
                    
                profile1 = behavior_profiles[act1]
                profile2 = behavior_profiles[act2]
                
                # Calculate similarity based on incoming/outgoing connections
                in_sim = len(profile1[0].intersection(profile2[0])) / max(1, len(profile1[0].union(profile2[0])))
                out_sim = len(profile1[1].intersection(profile2[1])) / max(1, len(profile1[1].union(profile2[1])))
                
                total_sim = (in_sim + out_sim) / 2
                if total_sim > self.min_bin_freq:
                    if act1 not in similarity_groups:
                        similarity_groups[act1] = {act1}
                    similarity_groups[act1].add(act2)
        
        # Create activity mapping for binning
        activity_mapping = {}
        for activity in activities:
            activity_mapping[activity] = activity
            
        # Apply grouping
        for rep_activity, group in similarity_groups.items():
            for activity in group:
                activity_mapping[activity] = rep_activity
        
        # Create new log with mapped activities
        new_log = {}
        for trace, frequency in log.items():
            new_trace = tuple(activity_mapping[act] for act in trace)
            if new_trace in new_log:
                new_log[new_trace] += frequency
            else:
                new_log[new_trace] = frequency
                
        return new_log
    
    def approximate_fallthrough(self, log):
        """Alternative fallthrough mechanism for the approximate miner.
        
        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies.
            
        Returns
        -------
        tuple
            A process tree representing an approximation.
        """
        log_alphabet = self.get_log_alphabet(log)
        
        # Handle empty traces
        if tuple() in log:
            empty_log = {tuple(): log[tuple()]}
            non_empty_log = {k: v for k, v in log.items() if k != tuple()}
            return ("xor", self.inductive_mining(empty_log), self.inductive_mining(non_empty_log))
            
        # For single activity case, possibly repeated
        if len(log_alphabet) == 1:
            activity = list(log_alphabet)[0]
            
            # Check if it appears multiple times in traces
            for trace in log:
                if trace.count(activity) > 1:
                    return ("loop", activity, "tau")
            
            return activity
            
        # For larger alphabets, simplify based on trace frequency
        if len(log) > 1:
            # Get the most frequent trace
            most_frequent_trace = max(log.items(), key=lambda x: x[1])[0]
            
            # If it represents a significant portion of the log
            total_freq = sum(log.values())
            if log[most_frequent_trace] / total_freq > 0.5:
                # Use it as the main path and create an xor with the rest
                main_log = {most_frequent_trace: log[most_frequent_trace]}
                other_log = {k: v for k, v in log.items() if k != most_frequent_trace}
                if other_log:
                    return ("xor", self.inductive_mining(main_log), self.inductive_mining(other_log))
        
        # Default to simpler flower model - limit the activities based on frequency
        activity_freq = self.appearance_frequency
        total_act_freq = sum(activity_freq.values())
        
        significant_activities = {act for act, freq in activity_freq.items() 
                                if freq / total_act_freq > self.min_bin_freq}
        
        if not significant_activities:
            significant_activities = log_alphabet
            
        return ("loop", "tau", *significant_activities)
        
    def get_simplification_threshold(self):
        """Get the simplification threshold.
        
        Returns
        -------
        float
            The simplification threshold.
        """
        return self.simplification_threshold
        
    def get_min_bin_freq(self):
        """Get the minimum binning frequency.
        
        Returns
        -------
        float
            The minimum binning frequency.
        """
        return self.min_bin_freq 