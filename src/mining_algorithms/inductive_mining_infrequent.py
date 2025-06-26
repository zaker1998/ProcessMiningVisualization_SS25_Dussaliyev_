from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.filters import filter_events, filter_traces
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
import copy


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
        self.logger.info("Start Inductive Mining Infrequent")
        process_tree = self.inductive_mining(self.filtered_log)
        
        from graphs.visualization.inductive_graph import InductiveGraph
        self.graph = InductiveGraph(
            process_tree,
            frequency=self.appearance_frequency,
            node_sizes=self.node_sizes
        )
    
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
        
        # Check if log is empty or has no activities
        if not log or all(len(trace) == 0 for trace in log):
            self.current_depth -= 1
            return "tau"
            
        if tree := self.base_cases(log):
            self.logger.debug(f"Base case: {tree}")
            self.current_depth -= 1
            return tree

        # Try to find a cut with noise filtering
        if tuple() not in log:
            # For high noise thresholds, we'll try special patterns first
            if self.noise_threshold > 0.3:
                if tree := self.try_high_noise_patterns(log):
                    self.current_depth -= 1
                    return tree
             
            # Create DFG with noise filtering
            dfg = self.create_filtered_dfg(log)
            
            # Try each type of cut with the filtered DFG in a safe way
            
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
                    
            # Parallel cut (using the existing implementation)
            if cut := parallel_cut(dfg):
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

        # Apply the fallthrough
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
    

    
    def try_high_noise_patterns(self, log):
        """Try to identify common patterns in noisy logs.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            The event log to analyze.

        Returns
        -------
        tuple or None
            A process tree representing the identified pattern, or None if no pattern is found.
        """
        activities = self.get_log_alphabet(log)
        
        # For very noisy logs with many variants, try to identify the main sequence
        if len(log) > 10 and len(activities) > 3:
            # Find most frequent trace
            most_frequent = max(log.items(), key=lambda x: x[1])
            if most_frequent[1] / sum(log.values()) > (1 - self.noise_threshold):
                return ("seq", *most_frequent[0])

        return None
    
    def create_filtered_dfg(self, log):
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
        # Create initial DFG
        dfg = DFG()
        
        # Add all events as nodes
        events = set()
        for trace in log:
            for event in trace:
                events.add(event)
        
        for event in events:
            dfg.add_node(event)
            
        # Calculate edge frequencies
        edge_frequencies = {}
        for trace, frequency in log.items():
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                if edge not in edge_frequencies:
                    edge_frequencies[edge] = 0
                edge_frequencies[edge] += frequency
                
        # Find maximum frequency
        max_frequency = max(edge_frequencies.values(), default=1)
        threshold = max_frequency * self.noise_threshold
        
        # Add edges that pass the threshold
        for (source, target), frequency in edge_frequencies.items():
            if frequency >= threshold:
                dfg.add_edge(source, target)
                
        return dfg
    
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
        log_alphabet = self.get_log_alphabet(log)

        # If there is an empty trace in the log
        if tuple() in log:
            # Special handling to avoid recursion issues
            return ("xor", "tau", self.create_simple_flower_model(log_alphabet))

        # If there is a single event in the log
        if len(log_alphabet) == 1:
            activity = list(log_alphabet)[0]
            
            # Check if it appears multiple times in traces
            for trace in log:
                if trace.count(activity) > 1:
                    return ("loop", activity, "tau")
                    
            return activity

        # Default approach: simple flower model
        return self.create_simple_flower_model(log_alphabet)
    
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
            
        return ("loop", "tau", *sorted(activities))
    
    def get_noise_threshold(self) -> float:
        """Get the noise threshold used for filtering directly-follows relations.

        Returns
        -------
        float
            The noise threshold
        """
        return self.noise_threshold 