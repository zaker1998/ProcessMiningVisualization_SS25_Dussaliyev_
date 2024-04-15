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
