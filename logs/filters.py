def filter_events(log, events_to_remove):
    filtered_log = {}
    for trace, frequency in log.items():
        filtered_trace = [event for event in trace if event not in events_to_remove]
        if len(filtered_trace) > 0:
            filtered_log[tuple(filtered_trace)] = (
                filtered_log.get(tuple(filtered_trace), 0) + frequency
            )

    return filtered_log
