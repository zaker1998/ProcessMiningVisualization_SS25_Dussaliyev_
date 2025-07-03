from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.filters import filter_events, filter_traces
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split


class InductiveMiningInfrequent(InductiveMining):
    """
    A class to generate a graph from a log using the Inductive Mining Infrequent algorithm.
    This hybrid variant first tries cuts on the full DFG to preserve structural information,
    then falls back to filtering infrequent directly-follows relations if cut quality is poor.
    This approach combines the benefits of information preservation and noise handling.
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
            
        # Track recursion depth
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
        """Hybrid approach: Try cuts on full DFG first, then fallback to filtered DFG."""
        self.logger.debug("Trying hybrid cut detection approach")
        
        # Step 1: Try cuts on full DFG (preserves all structural information)
        full_dfg = DFG(log)
        cut_result = self._try_all_cuts_on_dfg(full_dfg, log, "full")
        
        if cut_result and self._validate_cut_quality(cut_result, log):
            self.logger.debug(f"Found good cut on full DFG: {cut_result[0]}")
            return cut_result
        
        # Step 2: Fallback to filtered approach for noise handling
        self.logger.debug("Falling back to filtered DFG approach")
        filtered_dfg = self._create_filtered_dfg(log)
        cut_result = self._try_all_cuts_on_dfg(filtered_dfg, log, "filtered")
        
        if cut_result:
            self.logger.debug(f"Found cut on filtered DFG: {cut_result[0]}")
            return cut_result
        
        return None
    
    def _try_all_cuts_on_dfg(self, dfg, log, dfg_type):
        """Try all cut types on a given DFG."""
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
                    # Process each split recursively
                    sub_results = []
                    for split in splits:
                        sub_results.append(self.inductive_mining(split))
                    return (operation, *sub_results)
        
        return None
    
    def _validate_cut_quality(self, cut_result, log):
        """Validate the quality of a cut found on the full DFG.
        
        Parameters
        ----------
        cut_result : tuple
            The cut result (operation, *splits)
        log : dict
            The original log
            
        Returns
        -------
        bool
            True if the cut quality is acceptable, False otherwise
        """
        if not cut_result or len(cut_result) < 2:
            return False
            
        operation = cut_result[0]
        splits = cut_result[1:]
        
        # Quality checks based on cut type
        if operation == "xor":
            return self._validate_exclusive_cut_quality(splits, log)
        elif operation == "seq":
            return self._validate_sequence_cut_quality(splits, log)
        elif operation == "par":
            return self._validate_parallel_cut_quality(splits, log)
        elif operation == "loop":
            return self._validate_loop_cut_quality(splits, log)
        
        return True
    
    def _validate_exclusive_cut_quality(self, splits, log):
        """Validate exclusive cut quality - splits should be well-separated."""
        if len(splits) < 2:
            return False
            
        # Check that splits don't share too many activities (noise tolerance)
        split_activities = [self.get_log_alphabet(split) for split in splits]
        
        # Calculate overlap between splits
        total_overlaps = 0
        total_comparisons = 0
        
        for i in range(len(split_activities)):
            for j in range(i + 1, len(split_activities)):
                overlap = len(split_activities[i].intersection(split_activities[j]))
                union_size = len(split_activities[i].union(split_activities[j]))
                if union_size > 0:
                    overlap_ratio = overlap / union_size
                    total_overlaps += overlap_ratio
                    total_comparisons += 1
        
        if total_comparisons == 0:
            return True
            
        average_overlap = total_overlaps / total_comparisons
        # Accept if average overlap is below noise threshold
        return average_overlap <= self.noise_threshold
    
    def _validate_sequence_cut_quality(self, splits, log):
        """Validate sequence cut quality - splits should show clear ordering."""
        if len(splits) < 2:
            return False
            
        # Check that the ordering makes sense in terms of trace frequencies
        # Higher quality if splits appear in the expected order in most traces
        correct_order_count = 0
        total_traces = 0
        
        for trace, freq in log.items():
            if len(trace) < 2:
                continue
                
            total_traces += freq
            
            # Check if trace follows the expected sequence ordering
            split_positions = []
            for i, split in enumerate(splits):
                split_activities = self.get_log_alphabet(split)
                for j, activity in enumerate(trace):
                    if activity in split_activities:
                        split_positions.append((i, j))
                        break
            
            # Check if positions are in order
            if len(split_positions) >= 2:
                is_ordered = all(split_positions[i][0] <= split_positions[i+1][0] 
                               for i in range(len(split_positions)-1))
                if is_ordered:
                    correct_order_count += freq
        
        if total_traces == 0:
            return True
            
        order_ratio = correct_order_count / total_traces
        # Accept if most traces follow the expected order
        return order_ratio >= (1 - self.noise_threshold)
    
    def _validate_parallel_cut_quality(self, splits, log):
        """Validate parallel cut quality - splits should be truly concurrent."""
        if len(splits) < 2:
            return False
            
        # For parallel cuts, we expect activities from different splits
        # to appear in various orders (high variability)
        split_activities = [self.get_log_alphabet(split) for split in splits]
        
        # Check if splits contain distinct activities (good separation)
        all_activities = set()
        for activities in split_activities:
            if all_activities.intersection(activities):
                # Significant overlap between parallel splits might indicate poor cut
                overlap_size = len(all_activities.intersection(activities))
                if overlap_size > len(activities) * self.noise_threshold:
                    return False
            all_activities.update(activities)
        
        return True
    
    def _validate_loop_cut_quality(self, splits, log):
        """Validate loop cut quality - should have body and redo parts."""
        if len(splits) != 2:
            return False
            
        body, redo = splits
        
        # Basic loop validation already done in _is_valid_loop_split
        # Additional quality check: redo part should not be too large
        redo_activities = self.get_log_alphabet(redo)
        body_activities = self.get_log_alphabet(body)
        
        if not redo_activities or not body_activities:
            return False
            
        # Redo part should be smaller than body for good loop structure
        redo_ratio = len(redo_activities) / (len(redo_activities) + len(body_activities))
        return redo_ratio <= 0.6  # Redo should be at most 60% of total activities
    
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

        # Handle empty trace case - follow standard algorithm approach
        if tuple() in log:
            # Create a copy to avoid modifying the original log
            log_copy = log.copy()
            empty_log = {tuple(): log_copy[tuple()]}
            del log_copy[tuple()]
            return ("xor", self.inductive_mining(empty_log), self.inductive_mining(log_copy))

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