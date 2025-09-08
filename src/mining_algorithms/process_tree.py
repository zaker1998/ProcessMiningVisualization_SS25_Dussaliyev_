from enum import Enum
from typing import List, Optional, Dict, Any


class Operator(Enum):
    SEQUENCE = "seq"
    XOR = "xor"
    PARALLEL = "par"
    LOOP = "loop"
    TAU = "tau"
    ACTIVITY = "activity"


class ProcessTreeNode:
    """
    Simple process tree node used as canonical internal representation.

    - operator: Operator enum (ACTIVITY/TAU for leaves, others for internal nodes)
    - label: string label for ACTIVITY nodes
    - children: list of ProcessTreeNode
    """

    def __init__(
        self,
        operator: Optional[Operator] = None,
        label: Optional[str] = None,
        children: Optional[List["ProcessTreeNode"]] = None,
    ):
        self.operator = operator
        self.label = label
        self.children = children or []

    def __repr__(self) -> str:
        if self.operator == Operator.ACTIVITY:
            return f"Activity({self.label})"
        if self.operator == Operator.TAU:
            return "Tau"
        inner = ", ".join(repr(c) for c in self.children)
        return f"{self.operator.name}({inner})"

    def to_tuple(self) -> Any:
        """
        Convert node to legacy tuple/string format used by InductiveGraph:
        - 'tau' for tau,
        - 'act' string for activity,
        - ('seq', child1_tuple, child2_tuple, ...) for operators
        """
        if self.operator == Operator.TAU:
            return "tau"
        if self.operator == Operator.ACTIVITY:
            return self.label
        op = self.operator.value  # 'seq', 'xor', 'par', 'loop'
        
        # Validate that all children are ProcessTreeNode objects
        children_tuple = []
        for i, c in enumerate(self.children):
            if not isinstance(c, ProcessTreeNode):
                raise TypeError(
                    f"Child {i} of {self.operator.name} node is not a ProcessTreeNode: "
                    f"got {type(c).__name__} with value {c}. "
                    f"All children must be ProcessTreeNode objects."
                )
            children_tuple.append(c.to_tuple())
        
        return tuple([op, *children_tuple])