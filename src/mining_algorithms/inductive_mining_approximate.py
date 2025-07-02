from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.filters import filter_events, filter_traces
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split


class InductiveMiningApproximate(InductiveMining):
    """
    A class to generate a graph from a log using the Approximate Inductive Mining algorithm.
    This variant uses approximation strategies to handle complex or noisy logs.
    """

    def __init__(self, log):
        super().__init__(log)
        self.simplification_threshold = 0.1  # Default threshold for simplifying relations
    
    def generate_graph(self, activity_threshold=0.0, traces_threshold=0.2, 
                      simplification_threshold=0.1):
        """Generate a graph using the Approximate Inductive Mining algorithm.

        Parameters
        ----------
        activity_threshold : float
            The activity threshold for filtering of the log.
        traces_threshold : float
            The traces threshold for filtering of the log.
        simplification_threshold : float
            Threshold for simplifying directly-follows relations.
        """
        self.simplification_threshold = simplification_threshold
        
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
                operation = partitions[0]
                return (operation, *list(map(self.inductive_mining, partitions[1:])))

        # Use fallthrough if no cut found
        return self.fallthrough(log)

    def calculate_approximate_cut(self, log):
        """Find a partitioning of the log using simplified DFG for better noise handling.
        
        This is similar to the standard calulate_cut but uses a simplified DFG
        to better handle noisy or complex logs.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.

        Returns
        -------
        tuple | None
            A process tree representing the partitioning of the log if a cut was found, otherwise None.
        """
        # Create simplified DFG for better cut detection in noisy logs
        dfg = self.create_simplified_dfg(log)

        # Try cuts in the same order as standard inductive mining
        if partitions := exclusive_cut(dfg):
            return ("xor", *exclusive_split(log, partitions))
        elif partitions := sequence_cut(dfg):
            return ("seq", *sequence_split(log, partitions))
        elif partitions := parallel_cut(dfg):
            return ("par", *parallel_split(log, partitions))
        elif partitions := loop_cut(dfg):
            return ("loop", *loop_split(log, partitions))

        return None

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

        # For multiple events, create flower model (same as standard)
        # But limit complexity for very large alphabets
        if len(log_alphabet) > 10:
            # Use only the most frequent activities to avoid overly complex models
            activity_frequencies = {}
            for trace, freq in log.items():
                for activity in trace:
                    activity_frequencies[activity] = activity_frequencies.get(activity, 0) + freq
            
            # Keep top 10 most frequent activities
            top_activities = sorted(activity_frequencies.items(), key=lambda x: x[1], reverse=True)[:10]
            log_alphabet = {activity for activity, _ in top_activities}

        return ("loop", "tau", *sorted(log_alphabet)) 