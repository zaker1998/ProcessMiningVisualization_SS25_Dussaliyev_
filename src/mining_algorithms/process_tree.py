from enum import Enum
from typing import List, Optional

class Operator(Enum):
    SEQUENCE = "seq"
    XOR = "xor"
    PARALLEL = "and"
    LOOP = "loop"
    TAU = "tau"
    ACTIVITY = "activity"

class ProcessTreeNode:
    def __init__(
        self,
        operator: Optional[Operator] = None,
        label: Optional[str] = None,
        children: Optional[List['ProcessTreeNode']] = None
    ):
        self.operator = operator
        self.label = label
        self.children = children or []

    def __repr__(self):
        if self.operator == Operator.ACTIVITY:
            return f"Activity({self.label})"
        elif self.operator == Operator.TAU:
            return "Tau"
        else:
            return f"{self.operator.value.upper()}({', '.join(repr(child) for child in self.children)})"
