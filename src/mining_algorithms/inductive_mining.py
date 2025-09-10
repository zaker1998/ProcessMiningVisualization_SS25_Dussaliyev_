from typing import Dict, Tuple, List, Optional
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
from logs.filters import filter_events, filter_traces
from graphs.visualization.inductive_graph import InductiveGraph
from logger import get_logger
from mining_algorithms.process_tree import ProcessTreeNode, Operator
from mining_algorithms.base_mining import BaseMining

logger = get_logger("InductiveMining")


class InductiveMining(BaseMining):
    """
    Standard Inductive Mining implementation.
    Returns ProcessTreeNode internally, converts to legacy tuple before creating InductiveGraph.
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        super().__init__(log)
        self.logger = logger
        self.node_sizes = {}
        self.activity_threshold = 0.0
        self.traces_threshold = 0.2
        self.filtered_log: Optional[Dict[Tuple[str, ...], int]] = None

        # recursion safety
        self.max_recursion_depth = 100
        self.current_depth = 0

    def get_traces_threshold(self) -> float:
        """
        Get the current traces threshold value.
        
        Returns
        -------
        float
            The traces threshold value.
        """
        return self.traces_threshold
    
    def get_activity_threshold(self) -> float:
        """
        Get the current activity threshold value.
        
        Returns
        -------
        float
            The activity threshold value.
        """
        return self.activity_threshold

    # Public API
    def generate_graph(self, activity_threshold: float, traces_threshold: float):
        """
        Filter log by activity and trace thresholds and produce InductiveGraph.
        Keeps filtered_log cached to avoid recomputation.
        """
        self.activity_threshold = activity_threshold
        self.traces_threshold = traces_threshold

        # 1) Filter traces first
        min_traces_frequency = self.calculate_minimum_traces_frequency(traces_threshold)
        trace_filtered_log = filter_traces(self.log, min_traces_frequency)
        # 2) Compute event removals using frequencies from the trace-filtered log
        events_to_remove = self.get_events_to_remove_for_log(trace_filtered_log, activity_threshold)
        # 3) Apply event filtering
        filtered_log = filter_events(trace_filtered_log, events_to_remove)

        if filtered_log == self.filtered_log:
            self.logger.debug("Filtered log identical to previous, skipping.")
            return

        self.filtered_log = filtered_log
        # Compute node sizes only for events present in the filtered log
        filtered_events = self.get_log_alphabet(self.filtered_log)
        self.node_sizes = {k: self.calulate_node_size(k) for k in filtered_events}

        self.logger.info("Start Inductive Mining")
        process_tree = self._inductive_mining_internal(self.filtered_log)
        # Normalize the tree for readability and minimality
        process_tree = self._normalize_tree(process_tree)

        # keep internal representation
        self.process_tree = process_tree
        # convert to legacy representation for InductiveGraph
        process_tree_tuple = process_tree.to_tuple()
        self.graph = InductiveGraph(
            process_tree_tuple,
            frequency=self._build_frequency_map(),
            node_sizes=self.node_sizes,
        )

    # Core recursive miner
    def inductive_mining(self, log: Dict[Tuple[str, ...], int]):
        """
        Main recursive function. Returns legacy tuple format for compatibility with tests.
        """
        return self._inductive_mining_internal(log).to_tuple()

    def _inductive_mining_internal(self, log: Dict[Tuple[str, ...], int]) -> ProcessTreeNode:
        """
        Internal recursive function. Always returns a ProcessTreeNode.
        """
        # safety checks
        if not self._is_safe_to_continue(log):
            return self._safe_fallthrough(log)
        self.current_depth += 1

        try:
            if tree := self.base_cases(log):
                self.logger.debug(f"Base case: {tree}")
                return tree

            # only try cuts if no empty trace present
            if tuple() not in log:
                # try cuts in order: xor, seq, par, loop (preserve common priority)
                if partitions := self.calculate_cut(log):
                    op_str, splits = partitions
                    # basic split validation to avoid degenerate splits
                    if not self._basic_split_validation(splits, log):
                        self.logger.debug("Rejected cut due to poor split quality")
                    else:
                        children = [self._inductive_mining_internal(s) for s in splits]
                        op_map = {
                            "xor": Operator.XOR,
                            "seq": Operator.SEQUENCE,
                            "par": Operator.PARALLEL,
                            "loop": Operator.LOOP,
                        }
                        return ProcessTreeNode(operator=op_map[op_str], children=children)

            # fallthrough (flower/loop/xor with tau)
            return self.fallthrough(log)
        finally:
            self.current_depth -= 1

    # Base cases
    def base_cases(self, log: Dict[Tuple[str, ...], int]) -> Optional[ProcessTreeNode]:
        """
        If log has single trace with 0 or 1 activities, return tau or activity node.
        """
        if len(log) > 1:
            return None
        if len(log) == 1:
            trace = list(log.keys())[0]
            if len(trace) == 0:
                return ProcessTreeNode(operator=Operator.TAU)
            if len(trace) == 1:
                return ProcessTreeNode(operator=Operator.ACTIVITY, label=trace[0])
        return None

    # Cut calculation
    def calculate_cut(self, log: Dict[Tuple[str, ...], int]):
        """
        Try all cut types using DFG derived from log and return (operation_str, [splits...]) or None.
        Applies a light-weight split validation to avoid degenerate partitions.
        """
        dfg = DFG(log)
        if partitions := exclusive_cut(dfg):
            splits = exclusive_split(log, partitions)
            if self._basic_split_validation(splits, log):
                return ("xor", splits)
        if partitions := sequence_cut(dfg):
            splits = sequence_split(log, partitions)
            if self._basic_split_validation(splits, log):
                return ("seq", splits)
        if partitions := parallel_cut(dfg):
            splits = parallel_split(log, partitions)
            if self._basic_split_validation(splits, log):
                return ("par", splits)
        if partitions := loop_cut(dfg):
            splits = loop_split(log, partitions)
            if self._basic_split_validation(splits, log):
                return ("loop", splits)
        return None

    # Fallthrough & flower model
    def fallthrough(self, log: Dict[Tuple[str, ...], int]) -> ProcessTreeNode:
        """
        Fallback when no cut is found:
          - if empty trace exists -> XOR(tau, inductive_mining(rest))
          - if single activity alphabet -> LOOP(activity, tau)
          - otherwise -> flower model as LOOP with TAU + all activities
        """
        activities = self.get_log_alphabet(log)

        if tuple() in log:
            # copy to avoid mutation
            log_copy = dict(log)
            empty_log = {tuple(): log_copy[tuple()]}
            del log_copy[tuple()]
            return ProcessTreeNode(
                operator=Operator.XOR,
                children=[self._inductive_mining_internal(empty_log), self._inductive_mining_internal(log_copy)],
            )

        if len(activities) == 1:
            act = next(iter(activities))
            return ProcessTreeNode(
                operator=Operator.LOOP,
                children=[
                    ProcessTreeNode(operator=Operator.ACTIVITY, label=act),
                    ProcessTreeNode(operator=Operator.TAU),
                ],
            )

        # flower model -> LOOP with TAU and each activity as ACTIVITY child
        children = [ProcessTreeNode(operator=Operator.TAU)]
        for a in sorted(activities):
            children.append(ProcessTreeNode(operator=Operator.ACTIVITY, label=a))
        return ProcessTreeNode(operator=Operator.LOOP, children=children)

    def create_flower_model(self, activities: set, max_activities: Optional[int] = None):
        """
        Convenience factory creating flower model as ProcessTreeNode.
        """
        if not activities:
            return ProcessTreeNode(operator=Operator.TAU)
        if len(activities) == 1:
            return ProcessTreeNode(operator=Operator.ACTIVITY, label=next(iter(activities)))
        if max_activities is not None and len(activities) > max_activities:
            activities = set(sorted(activities)[:max_activities])
        children = [ProcessTreeNode(operator=Operator.TAU)]
        for a in sorted(activities):
            children.append(ProcessTreeNode(operator=Operator.ACTIVITY, label=a))
        return ProcessTreeNode(operator=Operator.LOOP, children=children)

    # Utility helpers
    def get_log_alphabet(self, log: Dict[Tuple[str, ...], int]) -> set:
        """Return set of events in provided log."""
        if log is None:
            return set()
        return set([event for case in log for event in case])

    def _is_safe_to_continue(self, log: Dict[Tuple[str, ...], int]) -> bool:
        """Basic safety checks to avoid runaway recursion."""
        if self.current_depth >= self.max_recursion_depth:
            self.logger.warning("Max recursion depth reached.")
            return False
        if not log or all(len(trace) == 0 for trace in log):
            return False
        return True

    def _safe_fallthrough(self, log: Dict[Tuple[str, ...], int]) -> ProcessTreeNode:
        """Return a safe fallback process tree."""
        activities = self.get_log_alphabet(log)
        return self.create_flower_model(activities)

    def _get_all_events(self) -> set:
        """Collect all unique events from the original log."""
        return set([ev for trace in self.log for ev in trace])

    def _build_frequency_map(self) -> Dict[str, int]:
        """Build appearance frequency map from initial log (for InductiveGraph usage)."""
        freq = {}
        for trace, f in self.log.items():
            for ev in trace:
                freq[ev] = freq.get(ev, 0) + f
        return freq

    def _create_tree_node(self, operator_str: str, children) -> ProcessTreeNode:
        """Create a ProcessTreeNode from operator string and children."""
        op_map = {
            "seq": Operator.SEQUENCE,
            "xor": Operator.XOR,
            "par": Operator.PARALLEL,
            "loop": Operator.LOOP,
        }
        
        child_nodes = []
        for child in children:
            if isinstance(child, str):
                if child == "tau":
                    child_nodes.append(ProcessTreeNode(operator=Operator.TAU))
                else:
                    child_nodes.append(ProcessTreeNode(operator=Operator.ACTIVITY, label=child))
            else:
                child_nodes.append(child)
        
        return ProcessTreeNode(operator=op_map[operator_str], children=child_nodes)

    def _basic_split_validation(self, splits: List[Dict[Tuple[str, ...], int]], original_log: Dict[Tuple[str, ...], int]) -> bool:
        """Light-weight validation to avoid degenerate splits."""
        if not splits or len(splits) < 2:
            return False
        total = 0
        for s in splits:
            if not s:
                return False
            total += sum(s.values())
        # Reject if more than 40% of frequency disappears due to splitting issues
        original = sum(original_log.values()) if original_log else 0
        if original and total < original * 0.6:
            return False
        return True

    def _normalize_tree(self, node: ProcessTreeNode) -> ProcessTreeNode:
        """Normalize the process tree by flattening same operators and removing redundant structures."""
        if node is None:
            return node
        if node.operator in {Operator.ACTIVITY, Operator.TAU}:
            return node
        # Normalize children first
        normalized_children: List[ProcessTreeNode] = [self._normalize_tree(c) for c in node.children]
        # Flatten nested same operators
        flattened: List[ProcessTreeNode] = []
        for c in normalized_children:
            if c.operator == node.operator and c.operator in {Operator.SEQUENCE, Operator.XOR, Operator.PARALLEL}:
                flattened.extend(c.children)
            else:
                flattened.append(c)
        # Remove single-child wrappers
        if len(flattened) == 1:
            return flattened[0]
        # Drop tau children for XOR if others exist
        if node.operator == Operator.XOR:
            non_tau = [c for c in flattened if c.operator != Operator.TAU]
            if non_tau:
                flattened = non_tau
                if len(flattened) == 1:
                    return flattened[0]
        return ProcessTreeNode(operator=node.operator, children=flattened)