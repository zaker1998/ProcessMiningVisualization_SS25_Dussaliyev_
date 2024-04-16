def exclusive_split(log: dict[tuple[str, ...], int], partitions: list[set[str]]):
    split_logs = [{} for _ in range(len(partitions))]
    for trace, frequency in log.items():
        # Skip empty traces
        if trace == tuple():
            continue
        for i, partition in enumerate(partitions):
            # Check if the trace is in the partition, when all events in the trace are in the partition
            # checking for one event would be enough, since the partition is exclusive, but to ensure correctness we check for all events
            if all(event in partition for event in trace):
                split_logs[i][trace] = frequency
                break

    return split_logs


def parallel_split(log: dict[tuple[str, ...], int], partitions: list[set[str]]):
    split_logs = [{} for _ in range(len(partitions))]
    for trace, frequency in log.items():
        sub_traces = [[] for _ in range(len(partitions))]
        if trace == tuple():
            continue
        for event in trace:
            for i, partition in enumerate(partitions):
                if event in partition:
                    sub_traces[i].append(event)
                    break

        for i, sub_trace in enumerate(sub_traces):
            split_logs[i][tuple(sub_trace)] = (
                split_logs[i].get(tuple(sub_trace), 0) + frequency
            )

    return split_logs


def sequence_split(log: dict[tuple[str, ...], int], partitions: list[set[str]]):
    split_logs = [{} for _ in range(len(partitions))]
    for trace, frequency in log.items():
        partition_iter = iter(partitions)
        sub_traces = [[] for _ in range(len(partitions))]
        if trace == tuple():
            continue

        current_partition = next(partition_iter)
        partition_index = 0
        for event in trace:
            while event not in current_partition:
                partition_index += 1
                current_partition = next(partition_iter)

            sub_traces[partition_index].append(event)

        for i, sub_trace in enumerate(sub_traces):
            split_logs[i][tuple(sub_trace)] = (
                split_logs[i].get(tuple(sub_trace), 0) + frequency
            )

    return split_logs


def loop_split(log: dict[tuple[str, ...], int], partitions: list[set[str]]):
    split_logs = [{} for _ in range(len(partitions))]
    for trace, frequency in log.items():
        if trace == tuple():
            continue

        sub_trace = []
        index = 0
        partition = partitions[0]
        for event in trace:
            if event not in partition:
                if len(sub_trace) > 0:
                    split_logs[index][tuple(sub_trace)] = (
                        split_logs[index].get(tuple(sub_trace), 0) + frequency
                    )
                    sub_trace = []
                index, partition = find_correct_partition(event, partitions)
            sub_trace.append(event)

        if len(sub_trace) > 0:
            split_logs[index][tuple(sub_trace)] = (
                split_logs[index].get(tuple(sub_trace), 0) + frequency
            )

    return split_logs


def find_correct_partition(event: str, partitions: list[set[str]]):
    for i, partition in enumerate(partitions):
        if event in partition:
            return i, partition
    # If the event is not in any partition, return -1 and an empty set
    # This should never happen, but is added for completeness
    return -1, set()
