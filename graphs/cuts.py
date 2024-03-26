from graphs.dfg import DFG


def exclusive_cut(graph: DFG) -> list[set[str | int], ...]:
    connected_components = graph.get_connected_components()
    return connected_components


def sequence_cut(graph: DFG) -> list[set[str | int], ...]:
    pass


def parallel_cut(graph: DFG) -> list[set[str | int], ...]:
    pass


def loop_cut(graph: DFG) -> list[set[str | int], ...]:
    pass
