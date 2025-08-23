from typing import Dict, Tuple, Optional
from graphs.dfg import DFG
from graphs.cuts import exclusive_cut, sequence_cut, parallel_cut, loop_cut
from logs.splits import exclusive_split, parallel_split, sequence_split, loop_split
from logger import get_logger
from process_tree import ProcessTreeNode, Operator
from mining_algorithms.inductive_mining import InductiveMining

logger = get_logger("InductiveMiningApproximate")


class InductiveMiningApproximate(InductiveMining):
    """
    Approximate variant that attempts cuts on the full DFG, and if cut quality
    is poor, falls back to a simplified DFG where low-frequency edges are removed.
    """

    def __init__(self, log: Dict[Tuple[str, ...], int]):
        super().__init__(log)
        self.simplification_threshold = 0.1

    def generate_graph(self, activity_threshold=0.0, traces_threshold=0.2, simplification_threshold=0.1):
        """Set simplification threshold and call parent generate_graph."""
        self.simplification_threshold = simplification_threshold
        super().generate_graph(activity_threshold, traces_threshold)

    def calculate_approximate_cut(self, log):
        full_dfg = DFG(log)

        if partitions := exclusive_cut(full_dfg):
            splits = exclusive_split(log, partitions)
            if self._validate_exclusive_cut_quality(splits, log):
                return (Operator.XOR, splits)

        if partitions := sequence_cut(full_dfg):
            splits = sequence_split(log, partitions)
            if self._validate_sequence_cut_quality(splits, log):
                return (Operator.SEQUENCE, splits)

        if partitions := parallel_cut(full_dfg):
            splits = parallel_split(log, partitions)
            if self._validate_parallel_cut_quality(splits, log):
                return (Operator.PARALLEL, splits)

        if partitions := loop_cut(full_dfg):
            splits = loop_split(log, partitions)
            if self._validate_loop_cut_quality(splits, log):
                return (Operator.LOOP, splits)

        # simplified dfg
        simp = self.create_simplified_dfg(log)

        if partitions := exclusive_cut(simp):
            return (Operator.XOR, exclusive_split(log, partitions))

        if partitions := sequence_cut(simp):
            return (Operator.SEQUENCE, sequence_split(log, partitions))

        if partitions := parallel_cut(simp):
            return (Operator.PARALLEL, parallel_split(log, partitions))

        if partitions := loop_cut(simp):
            return (Operator.LOOP, loop_split(log, partitions))

        return None

    def calulate_cut(self, log):
        """Override calulate_cut used by base class to plug in approximation logic."""
        return self.calculate_approximate_cut(log)

    def create_simplified_dfg(self, log):
        """
        Simplify DFG by removing edges below simplification_threshold * max_edge_frequency.
        """
        dfg = DFG(log)
        if self.simplification_threshold <= 0:
            return dfg

        # compute edge frequencies
        edge_freq = {}
        for trace, f in log.items():
            for i in range(len(trace) - 1):
                e = (trace[i], trace[i + 1])
                edge_freq[e] = edge_freq.get(e, 0) + f

        if not edge_freq:
            return dfg

        max_f = max(edge_freq.values())
        th = max_f * self.simplification_threshold

        simplified = DFG()
        for n in dfg.get_nodes():
            simplified.add_node(n)
        for e in dfg.get_edges():
            if edge_freq.get(e, 0) >= th:
                simplified.add_edge(e[0], e[1])

        # preserve start/end nodes if present
        try:
            simplified.start_nodes = dfg.start_nodes.copy()
            simplified.end_nodes = dfg.end_nodes.copy()
        except Exception:
            pass

        return simplified

    # quality validators (can be tuned/further improved)
    def _validate_exclusive_cut_quality(self, splits, log):
        if len(splits) < 2:
            return False
        split_activities = [set(self.get_log_alphabet(s)) for s in splits]
        total_overlaps = 0.0
        comparisons = 0
        for i in range(len(split_activities)):
            for j in range(i + 1, len(split_activities)):
                inter = len(split_activities[i].intersection(split_activities[j]))
                uni = len(split_activities[i].union(split_activities[j]))
                if uni > 0:
                    total_overlaps += inter / uni
                    comparisons += 1
        if comparisons == 0:
            return True
        avg = total_overlaps / comparisons
        return avg <= self.simplification_threshold

    def _validate_sequence_cut_quality(self, splits, log):
        if len(splits) < 2:
            return False
        correct = 0
        total = 0
        for trace, freq in log.items():
            if len(trace) < 2:
                continue
            total += freq
            pos = []
            for i, s in enumerate(splits):
                acts = set(self.get_log_alphabet(s))
                for j, a in enumerate(trace):
                    if a in acts:
                        pos.append((i, j))
                        break
            if len(pos) >= 2:
                ordered = all(pos[i][0] <= pos[i + 1][0] for i in range(len(pos) - 1))
                if ordered:
                    correct += freq
        if total == 0:
            return True
        return (correct / total) >= (1 - self.simplification_threshold)

    def _validate_parallel_cut_quality(self, splits, log):
        if len(splits) < 2:
            return False
        seen = set()
        for s in splits:
            acts = set(self.get_log_alphabet(s))
            if seen.intersection(acts):
                # heavy overlap => bad
                if len(seen.intersection(acts)) > len(acts) * self.simplification_threshold:
                    return False
            seen.update(acts)
        return True

    def _validate_loop_cut_quality(self, splits, log):
        if len(splits) != 2:
            return False
        body, redo = splits
        body_acts = set(self.get_log_alphabet(body))
        redo_acts = set(self.get_log_alphabet(redo))
        if not body_acts or not redo_acts:
            return False
        redo_ratio = len(redo_acts) / (len(body_acts) + len(redo_acts))
        max_ratio = 0.5 + self.simplification_threshold
        return redo_ratio <= max_ratio