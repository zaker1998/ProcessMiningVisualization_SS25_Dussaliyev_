from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, parallel_cut, sequence_cut, loop_cut
from logs.filters import filter_events, filter_traces


class InductiveMiningInfrequent(InductiveMining):
    """
    A class to generate a graph from a log using the Inductive Mining Infrequent algorithm.
    This variant filters infrequent directly-follows relations during cut detection.
    Implementation is designed to match PM4Py's behavior.
    """

    def __init__(self, log):
        super().__init__(log)
        self.noise_threshold = 0.2  # Default noise threshold
        
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
        super().generate_graph(activity_threshold, traces_threshold)
    
    def inductive_mining(self, log):
        """Generate a process tree from the log using the Inductive Mining Infrequent algorithm.
        This is a recursive function that generates the process tree from the log.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.

        Returns
        -------
        tuple
            A tuple representing the process tree.
        """
        if tree := self.base_cases(log):
            self.logger.debug(f"Base case: {tree}")
            return tree

        # Try to find a cut with noise filtering
        if tuple() not in log:
            if partitions := self.calulate_cut(log):
                self.logger.debug(f"Cut: {partitions}")
                operation = partitions[0]
                return (operation, *list(map(self.inductive_mining, partitions[1:])))

        return self.fallthrough(log)
    
    def calulate_cut(self, log) -> tuple | None:
        """Find a partitioning of the log using the different cut methods.
        Filters infrequent directly-follows relations before cut detection.

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
        
        # Filter infrequent directly-follows relations
        filtered_dfg = self.filter_infrequent_relations(dfg)
        
        # Try the different cuts
        if partitions := exclusive_cut(filtered_dfg):
            return ("xor", *self.exclusive_split(log, partitions))
        elif partitions := sequence_cut(filtered_dfg):
            return ("seq", *self.sequence_split(log, partitions))
        elif partitions := parallel_cut(filtered_dfg):
            return ("par", *self.parallel_split(log, partitions))
        elif partitions := loop_cut(filtered_dfg):
            return ("loop", *self.loop_split(log, partitions))

        return None
    
    def filter_infrequent_relations(self, dfg):
        """Filter infrequent directly-follows relations based on PM4Py's approach.
        
        Parameters
        ----------
        dfg : DFG
            The directly-follows graph.
            
        Returns
        -------
        DFG
            A new DFG with infrequent relations filtered out.
        """
        # Create a copy of the DFG
        filtered_dfg = DFG(dfg.log)
        
        # Find max relation frequency
        max_frequency = max(filtered_dfg.graph.values(), default=1)
        
        # Calculate threshold based on noise_threshold
        threshold = max_frequency * self.noise_threshold
        
        # Filter relations below threshold
        for (source, target), frequency in list(filtered_dfg.graph.items()):
            if frequency < threshold:
                del filtered_dfg.graph[(source, target)]
                
        return filtered_dfg
    
    def fallthrough(self, log):
        """Generate a process tree for the log using a fallthrough method.
        In Inductive Miner Infrequent, the fallthrough is adjusted to handle noise better.

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

        # if there is a empty trace in the log
        # make an xor split with tau and the inductive mining of the log without the empty trace
        if tuple() in log:
            empty_log = {tuple(): log[tuple()]}
            non_empty_log = {k: v for k, v in log.items() if k != tuple()}
            return ("xor", self.inductive_mining(empty_log), self.inductive_mining(non_empty_log))

        # if there is a single event in the log
        # and it occurs more than once in a trace
        # make a loop split with the event and tau
        if len(log_alphabet) == 1:
            activity = list(log_alphabet)[0]
            
            # Check if it appears multiple times in traces
            for trace in log:
                if trace.count(activity) > 1:
                    return ("loop", activity, "tau")
                    
            return activity

        # Analyze log to find most significant activities
        # This matches PM4Py's approach
        activity_freq = {activity: 0 for activity in log_alphabet}
        for trace, freq in log.items():
            for activity in set(trace): # Count each activity only once per trace
                activity_freq[activity] += freq
                
        total_freq = sum(activity_freq.values())
        
        # Filter out infrequent activities using noise threshold
        significant_activities = {act for act, freq in activity_freq.items() 
                               if freq / total_freq >= self.noise_threshold}
        
        # If no significant activities found, use all activities
        if not significant_activities:
            significant_activities = log_alphabet
        
        # Use a loop model with significant activities
        return ("loop", "tau", *significant_activities)
        
    def get_noise_threshold(self) -> float:
        """Get the noise threshold used for filtering directly-follows relations.
        
        Returns
        -------
        float
            The noise threshold
        """
        return self.noise_threshold 