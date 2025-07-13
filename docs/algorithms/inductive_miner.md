# Inductive Miner

The inductive miner is a recursive mining algorithm. It does not consider frequencies, but only looks at directly-follows relations. The algorithm uses an event log and creates a directly-follows graph from it. Through cuts in the graph, exclusive executions, parallel executions, sequential executions, and loops can be found. The algorithm produces sound process models, meaning every trace of the input log is represented in the model.

First, the algorithm checks for base cases, then it tries to find partitions in the directly-follows graphs. If a partition is found, the log is split in smaller logs and the algorithm is performed on them again until the algorithm terminates. If no cut is found or an empty trace is in the log, then a fall through is applied. In each recursion, a sub process tree is created. These trees are merged together to achieve the tree.

This implementation uses a small deviation from the described algorithm. Frequency is taken into account before the algorithm is run. To eliminate small outliers, infrequent events or traces can be removed. This was done to make the model easier readable and to find better cuts.

## Base Cases

First, the log is checked for a base case. Currently, there only exist two base cases, if the log is empty or only an empty trace is in the log, a silent activity, tau, is returned. This silent activity represents a silent transition, without an action. If there only exists one trace with exactly one event, then this event is returned. These are process trees with only one activity and will be the leafs of the final process tree. The base cases are one way to stop the recursive calls.

## Cuts

The second step is trying to find a cut in the directly-follows graph. There do exist 4 cuts in this implementation. The exclusive cut, the sequence cut, the parallel cut and the loop cut. If a cut is found, the log is split into multiple sublogs. The splitting depends on the found cut. Should an empty trace be in the log, cut detection is skipped and a fall through is applied. If, for cut detection, a partition of size one is found, a cut could not be detected and none is returned. The next cut will be performed until all cuts were checked.

### Exclusive Cut

The exclusive cut finds a partition in the graph, so that there does not exist an edge from one partition to any other partition. When all nodes are connected, no cut could be found and the algorithm checks for a sequence cut.

### Sequence Cut

The sequence cut is an order cut. It tries to find partitions so that there exists a path from a lower partition to a higher partition, but no path from the higher partition to the lower one. If only one partition was found, the algorithm checks for a parallel cut.

### Parallel Cut

The parallel cut shows that two partitions can be done concurrently. Every partition needs at least one start and one end event. A parallel cut is found if all nodes from one partition have an edge to all other nodes that are not in the partition. If no cut is found, the algorithm  tries to find a loop cut.

### Loop Cut

The last cut is the loop cut. It consists of a do part and one or multiple redo part. The do parts contains all start and end activities and represents a successful execution, the redo part does represent a failed execution. Redo parts always start at end activities and end at start activities. There does not exist an edge between multiple redo parts. Also, there does not exist an edge from a start activity to an activity of any redo partitions and there does not exist an edge from a redo partition to any end activities. Furthermore, if an activity from a redo partition has an edge from an end activity to itself, then all end activities need to have an edge to that activity.The same is true for edges to start activities. If no cut can be found, then a fall through is applied.

## Log Splitting

Each cut has its own rules on how to split the log. Each of the four log splitting procedures will be explained. The log will be split in a number of sublogs, that is equal to the number of partitions.

### Exclusive Split

The first split will be the exclusive split. Each trace is checked as a whole and will be assigned to one sublog. If the events of a trace are all in the same partition, then the trace will be added to the sublog of the partition.

### Sequence Split

The sequence split does split each trace in multiple subtraces and each subtrace will be assigned to a sublog. The algorithm starts with the first partition and an empty subtrace. While an event is part of the partition, the event will be added to the subtrace and the next element of the trace is checked. Should the element not be part of the partition, then the subtrace will be added to the sublog of the partition and a new empty subtrace will be created. The algorithm advances to the next partition and checks the event as previously described. This is done, until the full trace has been traversed. Should a trace not contain any events of a partition, then an empty trace is added to the sublog of the partition.

### Parallel Split

The parallel split does project each trace, for each partition. The projection only includes the events of the partitions in the projected trace, but keeps the relative order of the events. Should a trace not contain any elements of a partition, then an empty trace is projected.

### Loop Split

The loop split does split each trace in multiple subtraces and each subtrace will be assigned to a sublog. The algorithm starts with the first element and an empty subtrace. First, the partition of the current event needs to be found, and the event is added to the  subtrace. Then the next event is checked. As long as the events are in the same partition, they are added to the trace. If an event is not in the partition, the subtrace will be added to the sublog of the partition, an empty subtrace will be created, and the new partition will be found. These steps continue, until the end of the trace.

## Fall Through

The fall through is the last resort of the algorithm. If no cuts can be found, multiple fall through can be applied.

The first fall through checks if an empty trace is present in the log. Should this be the case, a process tree with the xor operation will be returned. The children will be tau, symbolizing a silent activity and the recursive call of the inductive miner on the log without the empty trace.

The second case occurs, when the log contains only one event, but it is executed more than once. Then a process tree, with a loop operation and the event and tau as children, will be returned. This process tree shows that the event can be executed more than once.

The last fall through is the flower model. This is a process tree, with the loop operator and tau as the first child and all other events in the log as other children. This shows that any order of execution is possible.

## Metrics

The algorithm uses two metrics, the activity threshold, and the traces threshold.

The activity threshold describes the frequency of an event in relation to the most frequent event. This metric is calculated, by dividing the frequency of the event by the maximum frequency of all the events.

The traces threshold describes the frequency of a trace in relation to the most frequent trace. This metric is calculated, by dividing the frequency of a trace by the maximum frequency of all traces.

## Filtering

Two metrics are used for filtering, the activity threshold, and the traces threshold.

The activity threshold is in the range of 0.0 and 1.0. It will remove activities/events from the log, that have a lower threshold than set.

The traces threshold is in the range of 0.0 and 1.0. It will remove traces from the log, that have a lower threshold than this parameter.

## Inductive Mining Infrequent

The Inductive Mining Infrequent variant is an extension of the basic Inductive Mining algorithm that filters out infrequent behavior directly from the directly-follows graph. This makes the algorithm more robust to noise in event logs, producing cleaner and more representative process models.

### Key Features

- **Noise Filtering**: Filters out infrequent directly-follows relations based on a configurable noise threshold
- **Hybrid Approach**: First attempts cuts on the full DFG to preserve structural information, then falls back to a filtered DFG if necessary
- **Adaptive Fallthrough**: Uses different fallthrough strategies based on the noise threshold level
- **PM4Py Compatibility**: Designed to match PM4Py's implementation behavior

### Noise Filtering Mechanism

The algorithm filters directly-follows relations whose frequency is below a threshold calculated as:
```
threshold = max_frequency * noise_threshold
```

Where:
- `max_frequency` is the frequency of the most common directly-follows relation
- `noise_threshold` is a parameter between 0 and 1 (higher values filter more aggressively)

### Cut Detection Strategy

The infrequent variant follows a two-step approach:

1. **Full DFG Analysis**: First attempts to find cuts on the complete directly-follows graph
2. **Filtered DFG Fallback**: If no good cut is found, creates a filtered DFG by removing infrequent edges and retries

This hybrid approach preserves as much structural information as possible while still handling noise effectively.

### Adaptive Fallthrough Behavior

When no cut can be found, the algorithm adapts its fallthrough strategy based on the noise threshold:

- **Low noise thresholds (≤ 0.3)**: Creates more flexible models with loops, allowing for more behavioral variation
- **High noise thresholds (> 0.3)**: Creates more structured models, focusing on the most frequent behavior patterns

### Usage

```python
from mining_algorithms.inductive_mining_infrequent import InductiveMiningInfrequent

miner = InductiveMiningInfrequent(log)
miner.generate_graph(
    activity_threshold=0.0,
    traces_threshold=0.0,
    noise_threshold=0.2  # Filter out edges with frequency < 20% of max
)
```

## Inductive Mining Approximate

The Inductive Mining Approximate variant is designed to handle complex and noisy event logs where the standard algorithm might produce overly complicated models. It uses simplification strategies to create more understandable process models while maintaining the essential behavior.

### Key Features

- **Simplification Threshold**: Uses a configurable threshold to determine when to simplify the directly-follows graph
- **Cut Quality Validation**: Validates the quality of cuts before accepting them
- **Complexity Limiting**: Limits model complexity for very large alphabets
- **Progressive Simplification**: Gradually simplifies the model if initial attempts fail

### Simplification Approach

The approximate variant creates a simplified directly-follows graph by:

1. Calculating edge frequencies from the event log
2. Removing edges with frequency below `max_frequency * simplification_threshold`
3. Preserving start and end node information

### Cut Quality Validation

Each cut type has specific quality validation criteria:

- **Exclusive Cut**: Checks for minimal overlap between partitions
- **Sequence Cut**: Validates that most traces follow the expected ordering
- **Parallel Cut**: Ensures limited overlap between parallel branches
- **Loop Cut**: Validates appropriate size ratio between body and redo parts

### Complexity Management

For logs with very large alphabets, the algorithm:
- Limits flower models to a maximum number of activities (default: 10)
- Uses the simplification threshold to reduce edge complexity
- Validates that cuts make meaningful progress in decomposition

### Usage

```python
from mining_algorithms.inductive_mining_approximate import InductiveMiningApproximate

miner = InductiveMiningApproximate(log)
miner.generate_graph(
    activity_threshold=0.0,
    traces_threshold=0.2,
    simplification_threshold=0.1,  # Simplify edges with frequency < 10% of max
    min_bin_freq=0.2  # Legacy parameter (not used)
)
```

## Comparison of Inductive Mining Variants

| Feature | Standard | Infrequent | Approximate |
|---------|----------|------------|-------------|
| **Primary Goal** | Discover sound process models | Handle noisy logs | Handle complex logs |
| **Noise Handling** | Pre-filtering only | Direct DFG filtering | Simplification strategy |
| **Main Parameter** | Activity/trace thresholds | Noise threshold | Simplification threshold |
| **DFG Approach** | Standard DFG | Filtered DFG (removes infrequent edges) | Simplified DFG (progressive simplification) |
| **Cut Detection** | Single attempt | Two-phase (full then filtered) | Two-phase with quality validation |
| **Cut Validation** | Basic validation | Basic validation | Quality-based validation |
| **Fallthrough** | Standard flower model | Adaptive based on noise level | Complexity-limited flower model |
| **Best Use Case** | Clean, well-structured logs | Logs with infrequent behavior | Complex logs with many activities |
| **Model Complexity** | Can be high | Reduced through filtering | Actively limited |
| **Information Loss** | Minimal (pre-filtering only) | Moderate (edge filtering) | Higher (simplification) |
| **Soundness** | Always sound | Always sound | Always sound |
| **PM4Py Compatibility** | N/A | Designed to match PM4Py | Custom implementation |

### Choosing the Right Variant

- **Use Standard Inductive Mining when:**
  - Your log is relatively clean and well-structured
  - You want to preserve all behavior in the log
  - Model complexity is not a major concern

- **Use Inductive Mining Infrequent when:**
  - Your log contains noise or infrequent exceptional behavior
  - You want to focus on the main process flow
  - You need compatibility with PM4Py results

- **Use Inductive Mining Approximate when:**
  - Your log is very complex with many activities
  - The standard algorithm produces overly complicated models
  - You prefer simpler, more understandable models
  - You can accept some loss of detail for clarity

### Parameter Guidelines

| Variant | Parameter | Range | Recommended Starting Value | Effect of Increasing |
|---------|-----------|-------|---------------------------|---------------------|
| All | activity_threshold | 0.0-1.0 | 0.0 | Removes more activities |
| All | traces_threshold | 0.0-1.0 | 0.2 | Removes more traces |
| Infrequent | noise_threshold | 0.0-1.0 | 0.2 | Filters more edges |
| Approximate | simplification_threshold | 0.0-1.0 | 0.1 | Simplifies more aggressively |

