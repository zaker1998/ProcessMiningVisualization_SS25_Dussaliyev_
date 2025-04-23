from mining_algorithms.inductive_mining import InductiveMining
from graphs.dfg import DFG
import random
from collections import Counter

class ApproximateInductiveMining(InductiveMining):
    """
    A class to generate a graph from a log using the Approximate Inductive Miner algorithm.
    This variant improves performance by sampling the log to reduce computational complexity.
    """

    def __init__(self, log):
        super().__init__(log)
        self.sample_size = 1000  # Default sample size
        self.sample_ratio = 0.0  # Default sample ratio - 0 means use sample_size instead
        
    def generate_graph(self, activity_threshold=0.0, traces_threshold=0.2, sample_size=1000, sample_ratio=0.0):
        """Generate a graph using the Approximate Inductive Miner algorithm.

        Parameters
        ----------
        activity_threshold : float
            The activity threshold for filtering of the log.
        traces_threshold : float
            The traces threshold for filtering of the log.
        sample_size : int
            The maximum number of traces to sample for mining.
            Larger sample sizes produce more accurate models but require more computation.
        sample_ratio : float
            If > 0, determines the percentage of the log to sample instead of using sample_size.
        """
        self.sample_size = sample_size
        self.sample_ratio = sample_ratio
        
        # Sample the log before proceeding with standard inductive mining
        sampled_log = self.sample_log(self.log)
        
        # Store the original log
        original_log = self.log
        # Replace log with sampled log temporarily
        self.log = sampled_log
        
        # Call the parent's generate_graph with the sampled log
        super().generate_graph(activity_threshold, traces_threshold)
        
        # Restore the original log
        self.log = original_log

    def sample_log(self, log):
        """Sample the log based on sample_size or sample_ratio.
        
        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.
            
        Returns
        -------
        dict[tuple[str, ...], int]
            A sampled version of the log.
        """
        if not log:
            return {}
            
        # Calculate the total number of traces
        total_traces = sum(log.values())
        
        # Determine how many traces to sample
        if self.sample_ratio > 0:
            num_samples = max(int(total_traces * self.sample_ratio), 1)
        else:
            num_samples = min(self.sample_size, total_traces)
            
        self.logger.info(f"Sampling {num_samples} traces from a log with {total_traces} total traces")
        
        # Create a list of all traces with repetition based on frequency
        all_traces = []
        for trace, freq in log.items():
            all_traces.extend([trace] * freq)
            
        # Sample randomly
        sampled_traces = random.sample(all_traces, num_samples)
        
        # Count frequencies of sampled traces
        sampled_log = dict(Counter(sampled_traces))
        
        return sampled_log
        
    def get_sample_size(self) -> int:
        """Get the sample size used for approximate mining.

        Returns
        -------
        int
            The sample size
        """
        return self.sample_size
        
    def get_sample_ratio(self) -> float:
        """Get the sample ratio used for sampling.
        
        Returns
        -------
        float
            The sample ratio
        """
        return self.sample_ratio

    def create_graph(self, process_tree):
        """Create the graph visualization from the process tree."""
        from graphs.visualization.inductive_graph import InductiveGraph
        return InductiveGraph(
            process_tree,
            frequency=self.appearance_frequency,
            node_sizes=self.node_sizes,
        )
        
    def filter_log(self, log):
        """Filter the log based on thresholds."""
        from logs.filters import filter_events, filter_traces
        
        # First filter events based on activity threshold
        filtered_log = filter_events(log, self.activity_threshold)
        
        # Then filter traces based on traces threshold
        filtered_log = filter_traces(filtered_log, self.traces_threshold)
        
        return filtered_log
        
    def get_sample_settings(self):
        """Get the sampling settings used.
        
        Returns
        -------
        dict
            Dictionary with sampling settings
        """
        return {
            "sample_size": self.sample_size,
            "sample_ratio": self.sample_ratio
        }

    def inductive_mining(self, log):
        """Apply Approximate Inductive Mining by sampling the log before mining.
        
        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.

        Returns
        -------
        tuple
            A tuple representing the process tree.
        """
        # Sample the log if it's larger than the sample size
        sampled_log = self._sample_log(log)
        
        # Use the standard inductive mining algorithm on the sampled log
        return super().inductive_mining(sampled_log)
    
    def _sample_log(self, log):
        """Sample the log to reduce its size for faster mining.
        
        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            A dictionary containing the traces and their frequencies in the log.
            
        Returns
        -------
        dict[tuple[str, ...], int]
            A sampled version of the input log.
        """
        # If log is already small enough, return it unchanged
        if sum(log.values()) <= self.sample_size:
            return log
            
        # Create a sampled version of the log based on trace frequencies
        sampled_log = {}
        traces = list(log.keys())
        frequencies = list(log.values())
        total_freq = sum(frequencies)
        
        # Calculate sampling probabilities based on trace frequencies
        probabilities = [freq / total_freq for freq in frequencies]
        
        # Sample traces with replacement according to their frequencies
        sampled_traces = random.choices(traces, weights=probabilities, k=min(self.sample_size, total_freq))
        
        # Count sampled traces
        for trace in sampled_traces:
            if trace in sampled_log:
                sampled_log[trace] += 1
            else:
                sampled_log[trace] = 1
                
        self.logger.info(f"Sampled log from {len(log)} unique traces to {len(sampled_log)} unique traces")
        
        return sampled_log 