from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, loop_cut
from logs.filters import filter_events, filter_traces
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
import numpy as np


class InductiveMiningApproximate(InductiveMining):
    """
    A class to generate a graph from a log using the Approximate Inductive Mining algorithm.
    This variant uses approximation strategies to handle complex or noisy logs.
    """

    def __init__(self, log):
        super().__init__(log)
        self.simplification_threshold = 0.1  # Default threshold for simplifying relations
        self.min_bin_freq = 0.2  # Default minimum frequency for binning activities
        self.max_recursion_depth = 20  # Prevent infinite recursion
        self.current_depth = 0  # Track current recursion depth
        self.processed_logs = set()  # Track processed logs to detect cycles
    
    def inductive_mining(self, log):
        """Generate a process tree from the log using the Approximate Inductive Mining algorithm.

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
        
        # Check for maximum recursion depth
        if self.current_depth > self.max_recursion_depth:
            self.logger.warning(f"Max recursion depth {self.max_recursion_depth} exceeded. Using fallthrough.")
            self.current_depth -= 1
            return self.create_simple_flower_model(self.get_log_alphabet(log))
            
        # Create a hash of the log to check for cycles
        log_hash = self._hash_log(log)
        if log_hash in self.processed_logs:
            self.logger.warning("Detected cycle in log processing. Using fallthrough.")
            self.current_depth -= 1
            return self.create_simple_flower_model(self.get_log_alphabet(log))
            
        self.processed_logs.add(log_hash)

        # Check base cases first
        if not log or all(len(trace) == 0 for trace in log):
            self.current_depth -= 1
            return "tau"
        
        if tree := self.base_cases(log):
            self.current_depth -= 1
            return tree
            
        # Try to find a cut
        if tuple() not in log:
            # Create simplified DFG
            dfg = self.create_simplified_dfg(log)
            
            # Try each cut type with safety checks
            # Exclusive cut (safe)
            if cut := exclusive_cut(dfg):
                splits = exclusive_split(log, cut)
                if splits and self._splits_progress(log, splits):
                    result = ("xor", *[self.inductive_mining(split) for split in splits])
                    self.current_depth -= 1
                    return result
                    
            # Sequence cut (safe)    
            if cut := sequence_cut(dfg):
                splits = sequence_split(log, cut)
                if splits and self._splits_progress(log, splits):
                    result = ("seq", *[self.inductive_mining(split) for split in splits])
                    self.current_depth -= 1
                    return result
                    
            # Safe parallel cut (using our custom implementation)
            if cut := self.safe_parallel_cut(dfg):
                splits = parallel_split(log, cut)
                if splits and self._splits_progress(log, splits):
                    result = ("par", *[self.inductive_mining(split) for split in splits])
                    self.current_depth -= 1
                    return result
        
            # Loop cut (safe) - especially careful with this one as it can cause recursion issues
            if cut := loop_cut(dfg):
                splits = loop_split(log, cut)
                if len(splits) == 2 and self._splits_progress(log, splits):
                    # Extra check for loop cut to avoid infinite recursion
                    if self._can_make_loop(splits[0], splits[1]):
                        result = ("loop", self.inductive_mining(splits[0]), self.inductive_mining(splits[1]))
                        self.current_depth -= 1
                        return result
        
        # If no cut is found, use fallthrough
        result = self.fallthrough(log)
        self.current_depth -= 1
        return result
        
    def _hash_log(self, log):
        """Create a hash representation of a log to detect cycles.

        Parameters
        ----------
        log : dict
            The log to hash

        Returns
        -------
        frozenset
            A hashable representation of the log
        """
        return frozenset((trace, freq) for trace, freq in log.items())
        
    def _splits_progress(self, original_log, splits):
        """Check if splits are making progress (not just recreating the original log).
        
        Parameters
        ----------
        original_log : dict
            The original log before splitting
        splits : list
            The list of split logs
            
        Returns
        -------
        bool
            True if splits are making progress, False otherwise
        """
        # If any split is empty, it's not making progress
        if any(not split for split in splits):
            return False
            
        # Check if splits are smaller than original
        original_size = sum(len(trace) * freq for trace, freq in original_log.items())
        for split in splits:
            split_size = sum(len(trace) * freq for trace, freq in split.items())
            # If any split is too close to original size, it might not be making progress
            if split_size > original_size * 0.9:
                # Further check to see if it's the same activities
                original_acts = self.get_log_alphabet(original_log)
                split_acts = self.get_log_alphabet(split)
                if split_acts == original_acts:
                    return False
        
        return True
        
    def _can_make_loop(self, body, redo):
        """Special check for loop cut to avoid infinite recursion.
        
        Parameters
        ----------
        body : dict
            The body part of the loop
        redo : dict
            The redo part of the loop
            
        Returns
        -------
        bool
            True if this is a valid loop structure, False otherwise
        """
        # Check if redo part contains activities
        redo_acts = self.get_log_alphabet(redo)
        if not redo_acts:
            return False
            
        # Check if body and redo share too many activities (could cause recursion)
        body_acts = self.get_log_alphabet(body)
        if len(body_acts.intersection(redo_acts)) > len(body_acts) * 0.8:
            return False
            
        return True
        
    def generate_graph(self, activity_threshold=0.0, traces_threshold=0.2, 
                      simplification_threshold=0.1, min_bin_freq=0.2):
        """Generate a graph using the Approximate Inductive Mining algorithm.

        Parameters
        ----------
        activity_threshold : float
            The activity threshold for filtering of the log.
        traces_threshold : float
            The traces threshold for filtering of the log.
        simplification_threshold : float
            Threshold for simplifying directly-follows relations.
        min_bin_freq : float
            Minimum frequency for binning activities with similar behavior.
        """
        self.simplification_threshold = simplification_threshold
        self.min_bin_freq = min_bin_freq
        self.current_depth = 0
        self.processed_logs = set()
        
        # Apply filtering first
        events_to_remove = self.get_events_to_remove(activity_threshold)
        min_traces_frequency = self.calulate_minimum_traces_frequency(traces_threshold)

        filtered_log = filter_traces(self.log, min_traces_frequency)
        filtered_log = filter_events(filtered_log, events_to_remove)

        if filtered_log == self.filtered_log:
            return

        self.filtered_log = filtered_log
        
        # Generate process tree and create graph
        self.logger.info("Start Approximate Inductive Mining")
        process_tree = self.inductive_mining(self.filtered_log)
        
        from graphs.visualization.inductive_graph import InductiveGraph
        self.graph = InductiveGraph(
            process_tree,
            frequency=self.appearance_frequency,
            node_sizes=self.node_sizes
        )

    def safe_parallel_cut(self, dfg):
        """A safer implementation of parallel cut detection.
        
        Parameters
        ----------
        dfg : DFG
            The directly-follows graph.
            
        Returns
        -------
        list or None
            A list of partitions, or None if no parallel cut is found.
        """
        # Get nodes from DFG
        nodes = list(dfg.get_nodes())
        if len(nodes) <= 1:
            return None
            
        # Find connected components
        visited = set()
        partitions = []
        
        # Simple connected components algorithm
        for node in nodes:
            if node in visited:
                continue
                
            # Start a new component
            component = {node}
            visited.add(node)
            
            # Find all nodes reachable from this node
            queue = [node]
            while queue:
                current = queue.pop(0)
                
                # Get successors and predecessors
                successors = dfg.get_successors(current)
                predecessors = dfg.get_predecessors(current)
                
                # Check for parallel relationship
                for other in nodes:
                    if other in visited or other == current:
                        continue
                        
                    # If there's no direct edge between nodes, they might be parallel
                    if (other not in successors and 
                        other not in predecessors):
                        
                        # Check if they have similar connections to other nodes
                        other_successors = dfg.get_successors(other)
                        other_predecessors = dfg.get_predecessors(other)
                        
                        # If they share similar connectivity patterns, add to component
                        if (successors.intersection(other_successors) or 
                            predecessors.intersection(other_predecessors)):
                            component.add(other)
                            visited.add(other)
                            queue.append(other)
            
            if component:
                partitions.append(component)
        
        # Only return partitions if we found more than one component
        if len(partitions) > 1:
            return partitions
            
        return None

    def create_simplified_dfg(self, log):
        """Create a DFG with approximation strategies applied.
        
        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            The event log to create the DFG from.
            
        Returns
        -------
        DFG
            The simplified directly-follows graph.
        """
        # Create initial DFG
        dfg = DFG()
        
        # Add all events as nodes
        events = set()
        for trace in log:
            for event in trace:
                events.add(event)
        
        for event in events:
            dfg.add_node(event)
            
        # Calculate edge frequencies and behavior profiles
        edge_frequencies = {}
        behavior_profiles = {act: (set(), set()) for act in events}  # (incoming, outgoing)
        
        for trace, frequency in log.items():
            for i in range(len(trace)):
                current = trace[i]
                # Record incoming edges
                if i > 0:
                    prev = trace[i-1]
                    edge = (prev, current)
                    edge_frequencies[edge] = edge_frequencies.get(edge, 0) + frequency
                    behavior_profiles[current][0].add(prev)
                # Record outgoing edges
                if i < len(trace) - 1:
                    next_act = trace[i+1]
                    behavior_profiles[current][1].add(next_act)
                    
        # Apply behavior-based binning for similar activities
        if len(events) > 5:  # Only apply binning for larger event sets
            binned_activities = self.bin_similar_activities(behavior_profiles)
            
            # Update edge frequencies based on binning
            new_frequencies = {}
            for (src, tgt), freq in edge_frequencies.items():
                new_src = binned_activities.get(src, src)
                new_tgt = binned_activities.get(tgt, tgt)
                new_edge = (new_src, new_tgt)
                new_frequencies[new_edge] = new_frequencies.get(new_edge, 0) + freq
            
            edge_frequencies = new_frequencies
                
        # Add edges that pass the threshold
        if edge_frequencies:
            max_frequency = max(edge_frequencies.values())
            threshold = max_frequency * self.simplification_threshold
            
            for (source, target), frequency in edge_frequencies.items():
                if frequency >= threshold:
                    dfg.add_edge(source, target)
                    
        return dfg

    def bin_similar_activities(self, behavior_profiles):
        """Bin activities with similar behavior patterns.
        
        Parameters
        ----------
        behavior_profiles : dict
            Dictionary mapping activities to their behavior profiles.
            
        Returns
        -------
        dict
            Mapping from original activities to their representative activities.
        """
        binned_activities = {}
        
        # Calculate similarity between activities
        activities = list(behavior_profiles.keys())
        for i, act1 in enumerate(activities):
            for act2 in activities[i+1:]:
                # Calculate similarity based on shared connections
                in_sim = len(behavior_profiles[act1][0].intersection(behavior_profiles[act2][0]))
                out_sim = len(behavior_profiles[act1][1].intersection(behavior_profiles[act2][1]))
                
                total_sim = (in_sim + out_sim) / max(1, len(behavior_profiles[act1][0]) + len(behavior_profiles[act1][1]))
                
                if total_sim >= self.min_bin_freq:
                    # Use the alphabetically first activity as representative
                    rep = min(act1, act2)
                    binned_activities[max(act1, act2)] = rep
                    
        return binned_activities

    def fallthrough(self, log):
        """Modified fallthrough method for approximate mining.
        
        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            The event log to process.
            
        Returns
        -------
        tuple
            A process tree representing an approximation.
        """
        # For small logs, try to find the most representative trace
        if len(log) <= 5:
            most_freq_trace = max(log.items(), key=lambda x: x[1])[0]
            if len(most_freq_trace) > 0:
                return ("seq", *most_freq_trace)
        
        # For larger logs, use a flower model with the most frequent activities
        activities = self.get_log_alphabet(log)
        
        # Create a simple flower model
        return self.create_simple_flower_model(activities)
        
    def create_simple_flower_model(self, activities):
        """Create a simple flower model with the given activities.
        
        Parameters
        ----------
        activities : set
            The set of activities to include in the model.
        
        Returns
        -------
        tuple
            A process tree representing a flower model.
        """
        if not activities:
            return "tau"
            
        if len(activities) == 1:
            return list(activities)[0]
        
        # For larger activity sets, limit to most frequent ones to avoid overly complex models
        if len(activities) > 4:
            # Calculate activity frequencies
            act_freq = {act: sum(freq for trace, freq in self.filtered_log.items() if act in trace)
                      for act in activities}
            
            # Keep only the most frequent activities
            top_activities = sorted(act_freq.items(), key=lambda x: x[1], reverse=True)[:4]
            activities = {act for act, _ in top_activities}
            
        return ("loop", "tau", *sorted(activities)) 