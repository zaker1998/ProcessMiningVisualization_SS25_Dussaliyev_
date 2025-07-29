from enum import Enum
from typing import List, Optional

class Operator(Enum):
    SEQUENCE = "seq"
    XOR = "xor"
    PARALLEL = "and"
    LOOP = "loop"
    TAU = "tau"
    ACTIVITY = "activity"