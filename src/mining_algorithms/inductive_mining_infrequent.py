from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.filters import filter_events, filter_traces
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split


class InductiveMiningInfrequent(InductiveMining):
    """
    A class to generate a graph from a log using the Inductive Mining Infrequent algorithm.
    This variant filters infrequent directly-follows relations during cut detection.
    Implementation is designed to match PM4Py's behavior.
    """

    def __init__(self, log):
        super().__init__(log)
        self.noise_threshold = 0.2  # Default noise threshold
        self.max_recursion_depth = 20  # Prevent infinite recursion
        self.current_depth = 0  # Track current recursion depth
        self.processed_logs = set()  # Track processed logs to prevent cycles
        
    def generate_graph(self, activity_threshold=0.0, traces_threshold=0.2, noise_threshold=0.2):
        """Generate a graph using the Inductive Mining Infrequent algorithm.

        Parameters
        ----------
        activity_threshold : float
            The activity threshold for filtering of the log.
        traces_threshold : float
            The traces threshold for filtering of the log.
        noise_threshold : float
            The noise threshold for filtering directly-follows relations.
            Directly-follows relations with a frequency lower than threshold * max_relation_frequency will be ignored.
        """
        self.noise_threshold = noise_threshold
        self._reset_state()
        
        # Apply filtering first
        events_to_remove = self.get_events_to_remove(activity_threshold)
        min_traces_frequency = self.calulate_minimum_traces_frequency(traces_threshold)

        filtered_log = filter_traces(self.log, min_traces_frequency)
        filtered_log = filter_events(filtered_log, events_to_remove)

        if filtered_log == self.filtered_log:
            return

        self.filtered_log = filtered_log
        
        # Generate process tree and create graph
        self.logger.info("Start Inductive Mining Infrequent")
        process_tree = self.inductive_mining(self.filtered_log)
        
        from graphs.visualization.inductive_graph import InductiveGraph
        self.graph = InductiveGraph(
            process_tree,
            frequency=self.appearance_frequency,
            node_sizes=self.node_sizes
        )
    
    def _reset_state(self):
        """Reset internal state for a new mining operation."""
        self.current_depth = 0
        self.processed_logs = set()
    
    def inductive_mining(self, log):
        """Generate a process tree from the log using the Inductive Mining Infrequent algorithm.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.

        Returns
        -------
        tuple
            A tuple representing the process tree.
        """
        # Safety checks
        if not self._is_safe_to_continue(log):
            return self._safe_fallthrough(log)
            
        # Mark this log as processed
        log_hash = frozenset(log.items())
        self.processed_logs.add(log_hash)
        self.current_depth += 1
        
        try:
            # Check base cases first
            if tree := self.base_cases(log):
                self.logger.debug(f"Base case: {tree}")
                return tree

            # Try cuts only if no empty trace exists
            if tuple() not in log:
                tree = self._try_cuts_with_noise_filtering(log)
                if tree:
                    return tree

            # Apply fallthrough
            return self.fallthrough(log)
            
        finally:
            self.current_depth -= 1
    
    def _is_safe_to_continue(self, log):
        """Check if it's safe to continue processing this log."""
        # Check recursion depth
        if self.current_depth >= self.max_recursion_depth:
            self.logger.warning(f"Max recursion depth {self.max_recursion_depth} exceeded.")
            return False
            
        # Check for cycles
        log_hash = frozenset(log.items())
        if log_hash in self.processed_logs:
            self.logger.warning("Detected cycle in log processing.")
            return False
            
        # Check if log is empty or has no activities
        if not log or all(len(trace) == 0 for trace in log):
            return False
            
        return True
    
    def _safe_fallthrough(self, log):
        """Safe fallthrough that handles edge cases."""
        if not log:
            return "tau"
        
        activities = self.get_log_alphabet(log)
        if not activities:
            return "tau"
        elif len(activities) == 1:
            return list(activities)[0]
        else:
            return ("loop", "tau", *sorted(activities))
    
    def _try_cuts_with_noise_filtering(self, log):
        """Try all cut types with noise filtering applied."""
        # Create filtered DFG
        dfg = self._create_filtered_dfg(log)
        
        # Try cuts in order of preference
        cut_methods = [
            (exclusive_cut, exclusive_split, "xor"),
            (sequence_cut, sequence_split, "seq"),
            (parallel_cut, parallel_split, "par"),
            (loop_cut, loop_split, "loop")
        ]
        
        for cut_func, split_func, operation in cut_methods:
            if cut := cut_func(dfg):
                splits = split_func(log, cut)
                if self._are_splits_valid(log, splits, operation):
                    return (operation, *[self.inductive_mining(split) for split in splits])
        
        return None
    
    def _are_splits_valid(self, original_log, splits, operation):
        """Check if the splits are valid and making progress."""
        if not splits or any(not split for split in splits):
            return False
            
        # Special validation for loop cuts to prevent infinite recursion
        if operation == "loop" and len(splits) == 2:
            return self._is_valid_loop_split(splits[0], splits[1])
            
        # General progress check
        return self._splits_make_progress(original_log, splits)
    
    def _splits_make_progress(self, original_log, splits):
        """Check if splits are making meaningful progress."""
        original_size = sum(len(trace) * freq for trace, freq in original_log.items())
        original_activities = self.get_log_alphabet(original_log)
        
        for split in splits:
            split_size = sum(len(trace) * freq for trace, freq in split.items())
            split_activities = self.get_log_alphabet(split)
            
            # If split is too similar to original, it's not making progress
            if (split_size > original_size * 0.9 and 
                split_activities == original_activities):
                return False
        
        return True
        
    def _is_valid_loop_split(self, body, redo):
        """Validate loop split to avoid infinite recursion."""
        redo_activities = self.get_log_alphabet(redo)
        if not redo_activities:
            return False
            
        body_activities = self.get_log_alphabet(body)
        overlap = len(body_activities.intersection(redo_activities))
        
        # Too much overlap might cause recursion issues
        return overlap <= len(body_activities) * 0.8
    
    def _create_filtered_dfg(self, log):
        """Create a DFG with noise filtering applied.
        
        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            The event log to create the DFG from.
            
        Returns
        -------
        DFG
            The filtered directly-follows graph.
        """
        dfg = DFG()
        
        # Add all events as nodes
        activities = self.get_log_alphabet(log)
        for activity in activities:
            dfg.add_node(activity)
            
        # Calculate edge frequencies and apply noise filtering
        edge_frequencies = self._calculate_edge_frequencies(log)
        if not edge_frequencies:
            return dfg
            
        max_frequency = max(edge_frequencies.values())
        threshold = max_frequency * self.noise_threshold
        
        # Add edges that pass the threshold
        for (source, target), frequency in edge_frequencies.items():
            if frequency >= threshold:
                dfg.add_edge(source, target)
                
        return dfg
    
    def _calculate_edge_frequencies(self, log):
        """Calculate the frequency of each edge in the log."""
        edge_frequencies = {}
        
        for trace, frequency in log.items():
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                edge_frequencies[edge] = edge_frequencies.get(edge, 0) + frequency
                
        return edge_frequencies
    
    def fallthrough(self, log):
        """Generate a process tree for the log using a fallthrough method.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.

        Returns
        -------
        tuple
            A tuple representing the process tree.
        """
        activities = self.get_log_alphabet(log)

        # Handle empty trace case
        if tuple() in log:
            return ("xor", "tau", self._create_flower_model(activities))

        # Handle single activity case
        if len(activities) == 1:
            activity = list(activities)[0]
            # Check if it appears multiple times in any trace
            for trace in log:
                if trace.count(activity) > 1:
                    return ("loop", activity, "tau")
            return activity

        # Default: flower model
        return self._create_flower_model(activities)
    
    def _create_flower_model(self, activities):
        """Create a flower model with the given activities."""
        if not activities:
            return "tau"
        elif len(activities) == 1:
            return list(activities)[0]
        else:
            return ("loop", "tau", *sorted(activities)) 