from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, parallel_cut, sequence_cut, loop_cut


class InductiveMiningInfrequent(InductiveMining):
    """
    A class to generate a graph from a log using the Inductive Mining Infrequent algorithm.
    This variant filters infrequent directly-follows relations during cut detection.
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
    
    def calulate_cut(self, log) -> tuple | None:
        """Find a partitioning of the log using the different cut methods.
        This override filters infrequent directly-follows relations before cut detection.

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
        # Create a copy of the DFG
        filtered_dfg = DFG(dfg.log)
        
        # Find max relation frequency
        max_frequency = max(filtered_dfg.graph.values(), default=1)
        threshold = max_frequency * self.noise_threshold
        
        # Filter relations below threshold
        for (source, target), frequency in list(filtered_dfg.graph.items()):
            if frequency < threshold:
                del filtered_dfg.graph[(source, target)]
                
        return filtered_dfg
        
    def get_noise_threshold(self) -> float:
        """Get the noise threshold used for filtering directly-follows relations.
        
        Returns
        -------
        float
            The noise threshold
        """
        return self.noise_threshold 