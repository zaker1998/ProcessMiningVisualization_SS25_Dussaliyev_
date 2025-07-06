from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.filters import filter_events, filter_traces
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split


class InductiveMiningApproximate(InductiveMining):
    """
    A class to generate a graph from a log using the Approximate Inductive Mining algorithm.
    This hybrid variant first tries cuts on the full DFG to preserve structural information,
    then falls back to simplification strategies if cut quality is poor.
    This approach balances information preservation with noise handling for complex logs.
    """

    def __init__(self, log):
        super().__init__(log)
        self.simplification_threshold = 0.1  # Default threshold for simplifying relations
    
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
            Minimum frequency for binning activities (kept for backward compatibility, not used).
        """
        self.simplification_threshold = simplification_threshold
        # min_bin_freq parameter kept for backward compatibility but not used
        
        # Apply filtering first (same as standard inductive mining)
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

    def inductive_mining(self, log):
        """Generate a process tree from the log using the Approximate Inductive Mining algorithm.
        
        This follows the same pattern as standard inductive mining but uses a simplified DFG
        for cut detection to handle noisy logs better.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.

        Returns
        -------
        tuple
            A tuple representing the process tree.
        """
        # Check base cases first (same as standard)
        if tree := self.base_cases(log):
            self.logger.debug(f"Base case: {tree}")
            return tree

        # Try to find cuts (with approximation for complex logs)
        if tuple() not in log:
            if partitions := self.calculate_approximate_cut(log):
                self.logger.debug(f"Cut: {partitions}")
                return partitions

        # Use fallthrough if no cut found
        return self.fallthrough(log)

    def calculate_approximate_cut(self, log):
        """Hybrid approach: Try cuts on full DFG first, then fallback to simplified DFG.
        
        This preserves structural information while providing fallback simplification
        for complex or noisy logs when the full approach doesn't yield good cuts.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.

        Returns
        -------
        tuple | None
            A process tree representing the partitioning of the log if a cut was found, otherwise None.
        """
        self.logger.debug("Trying hybrid cut detection approach")
        
        # Step 1: Try cuts on full DFG (preserves all structural information)
        full_dfg = DFG(log)
        cut_result = self._try_all_cuts_on_dfg(full_dfg, log, "full")
        
        if cut_result and self._validate_cut_quality(cut_result, log):
            self.logger.debug(f"Found good cut on full DFG: {cut_result[0]}")
            return cut_result
        
        # Step 2: Fallback to simplified approach for complex/noisy logs
        self.logger.debug("Falling back to simplified DFG approach")
        simplified_dfg = self.create_simplified_dfg(log)
        cut_result = self._try_all_cuts_on_dfg(simplified_dfg, log, "simplified")
        
        if cut_result:
            self.logger.debug(f"Found cut on simplified DFG: {cut_result[0]}")
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
            if partitions := cut_func(dfg):
                splits = split_func(log, partitions)
                if splits and self._are_splits_valid(log, splits, operation):
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
        
        # Quality checks based on cut type and simplification threshold
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
        """Validate exclusive cut quality using simplification threshold."""
        if len(splits) < 2:
            return False
            
        # Check that splits don't share too many activities (complexity tolerance)
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
        # Accept if average overlap is below simplification threshold
        return average_overlap <= self.simplification_threshold
    
    def _validate_sequence_cut_quality(self, splits, log):
        """Validate sequence cut quality using simplification threshold."""
        if len(splits) < 2:
            return False
            
        # Similar to infrequent but using simplification_threshold
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
        return order_ratio >= (1 - self.simplification_threshold)
    
    def _validate_parallel_cut_quality(self, splits, log):
        """Validate parallel cut quality using simplification threshold."""
        if len(splits) < 2:
            return False
            
        split_activities = [self.get_log_alphabet(split) for split in splits]
        
        # Check for excessive overlap between parallel splits
        all_activities = set()
        for activities in split_activities:
            if all_activities.intersection(activities):
                overlap_size = len(all_activities.intersection(activities))
                if overlap_size > len(activities) * self.simplification_threshold:
                    return False
            all_activities.update(activities)
        
        return True
    
    def _validate_loop_cut_quality(self, splits, log):
        """Validate loop cut quality using simplification threshold."""
        if len(splits) != 2:
            return False
            
        body, redo = splits
        redo_activities = self.get_log_alphabet(redo)
        body_activities = self.get_log_alphabet(body)
        
        if not redo_activities or not body_activities:
            return False
            
        # Use simplification threshold to determine acceptable redo size
        redo_ratio = len(redo_activities) / (len(redo_activities) + len(body_activities))
        max_redo_ratio = 0.5 + self.simplification_threshold  # More flexible with higher threshold
        return redo_ratio <= max_redo_ratio
    
    def _are_splits_valid(self, original_log, splits, operation):
        """Check if the splits are valid and making progress."""
        if not splits or any(not split for split in splits):
            return False
            
        # Special validation for loop cuts
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
        
        # Use simplification threshold for overlap tolerance
        max_overlap_ratio = 0.7 + self.simplification_threshold * 0.2
        return overlap <= len(body_activities) * max_overlap_ratio

    def create_simplified_dfg(self, log):
        """Create a DFG with noise filtering applied.
        
        This creates a standard DFG but filters out low-frequency edges
        to reduce noise and improve cut detection.
        
        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            The event log to create the DFG from.
            
        Returns
        -------
        DFG
            The simplified directly-follows graph.
        """
        # Create standard DFG first
        dfg = DFG(log)
        
        # If simplification threshold is 0, return standard DFG
        if self.simplification_threshold <= 0:
            return dfg
            
        # Calculate edge frequencies for filtering
        edge_frequencies = {}
        for trace, frequency in log.items():
            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                edge_frequencies[edge] = edge_frequencies.get(edge, 0) + frequency
        
        if not edge_frequencies:
            return dfg
            
        # Calculate threshold for edge filtering
        max_frequency = max(edge_frequencies.values())
        threshold = max_frequency * self.simplification_threshold
        
        # Create new simplified DFG
        simplified_dfg = DFG()
        
        # Add all nodes
        for node in dfg.get_nodes():
            simplified_dfg.add_node(node)
            
        # Add only edges that meet the threshold
        for edge in dfg.get_edges():
            if edge_frequencies.get(edge, 0) >= threshold:
                simplified_dfg.add_edge(edge[0], edge[1])
                
        # Ensure start and end nodes are preserved
        simplified_dfg.start_nodes = dfg.start_nodes.copy()
        simplified_dfg.end_nodes = dfg.end_nodes.copy()
        
        return simplified_dfg

    def fallthrough(self, log):
        """Generate a process tree for the log using fallthrough method.
        
        Uses the same fallthrough logic as standard inductive mining
        but with better handling for complex logs.
        
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

        # Handle empty trace case (same as standard)
        if tuple() in log:
            empty_log = {tuple(): log[tuple()]}
            del log[tuple()]
            return ("xor", self.inductive_mining(empty_log), self.inductive_mining(log))

        # Handle single event case (same as standard)
        if len(log_alphabet) == 1:
            return ("loop", list(log_alphabet)[0], "tau")

        # For multiple events, create flower model with complexity limiting
        # Limit to 10 activities for very large alphabets to avoid overly complex models
        return self.create_flower_model(log_alphabet, max_activities=10) 