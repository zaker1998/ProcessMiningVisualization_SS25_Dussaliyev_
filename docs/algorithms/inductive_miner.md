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

## Inductive Mining Infrequent (IMf)

The Inductive Mining Infrequent (IMf) variant based on the 2014 paper by Leemans et al. It extends the standard Inductive Mining algorithm to handle noisy event logs by filtering infrequent behavior when necessary.

### Scientific Reference

**Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P. (2014):**  
*Discovering Block-Structured Process Models from Event Logs Containing Infrequent Behaviour.*  
Business Process Management Workshops. BPM 2013. Lecture Notes in Business Information Processing, vol 171. Springer, Cham.  
DOI: 10.1007/978-3-319-06257-0_6

### Key Features

- **Sound Process Models**: Guaranteed no deadlocks or anomalies
- **Rediscoverability**: Can recover original model from sufficiently complete logs (under noise threshold)
- **Two-Phase Approach**: Tries full DFG first (preserve information), then filtered DFG (handle noise)
- **Canonical Algorithm**: Follows the 2014 paper specification
- **PM4Py Comparable**: Designed to produce comparable results to PM4Py's implementation

### Algorithm Overview

IMf follows a **two-phase cut detection strategy**:

**Phase 1: Full DFG Analysis**
- Attempts to find cuts on the complete directly-follows graph
- Preserves all structural information
- Succeeds when log is clean or noise doesn't affect structure

**Phase 2: Filtered DFG Analysis** (only if Phase 1 fails)
- Filters edges with frequency < (noise_threshold × max_edge_frequency)
- Retries cut detection on filtered DFG
- Enables discovery in noisy logs

### Noise Filtering Mechanism

Edge filtering threshold calculation:
```
threshold = max_edge_frequency × noise_threshold
```

Where:
- `max_edge_frequency`: Frequency of the most common directly-follows relation
- `noise_threshold`: Parameter between 0.0 and 1.0 (recommended: 0.2)

**Example:**  
If max edge frequency is 100 and noise_threshold=0.2, then edges with frequency < 20 are filtered.

### Cut Detection Order

The algorithm tries cuts in this canonical order:
1. **Exclusive (XOR)**: Disconnected components in DFG
2. **Sequence (→)**: Ordered execution based on reachability
3. **Parallel (∧)**: Concurrent execution (inverted DFG analysis)
4. **Loop (↻)**: Repetitive structure with do/redo parts

### Usage

```python
from mining_algorithms.inductive_mining_infrequent import InductiveMiningInfrequent

# Create miner instance
miner = InductiveMiningInfrequent(log)

# Run discovery with canonical parameters
miner.generate_graph(
    activity_threshold=0.0,   # Pre-filter: remove rare activities
    traces_threshold=0.0,     # Pre-filter: remove rare traces
    noise_threshold=0.2       # Canonical default: filter edges < 20% of max
)

# Get discovered process tree
process_tree = miner.get_graph()
```

### Parameter Guidance

| noise_threshold | Effect | When to Use |
|----------------|--------|-------------|
| 0.0 | No edge filtering (equivalent to standard IM) | Clean logs with no noise |
| 0.1 | Light filtering | Minor noise (< 10% of max edge frequency) |
| **0.2** | **Recommended default** | **Typical noisy logs** |
| 0.3-0.5 | Moderate filtering | Significant noise |
| > 0.5 | Aggressive filtering | Very noisy logs (may lose important behavior) |

### Properties and Guarantees

- **Soundness**: Always produces sound process models
- **Rediscoverability**: Yes (given sufficiently complete log under noise threshold)
- **Complexity**: Exponential in worst case, polynomial in practice for structured logs
- **Memory**: O(log size) - requires full log in memory
- **Recommended for**: Logs with < 10⁶ traces and < 1000 activities

## Inductive Mining Directly-Follows (IMd)

The Inductive Mining Directly-Follows (IMd) variant based on the 2018 paper by Leemans et al. It is designed for **scalability** - handling event logs with billions of events and thousands of activities.

### Scientific Reference

**Leemans, S.J.J., Fahland, D., van der Aalst, W.M.P. (2018):**  
*Scalable process discovery and conformance checking.*  
Software & Systems Modeling 17, 599–631.  
DOI: 10.1007/s10270-016-0545-x

### Key Features

- **Extreme Scalability**: Can handle billions of events (10⁹+) and thousands of activities
- **Single-Pass Processing**: Streams through log once to build DFG
- **Memory Efficient**: O(|activities|²) memory complexity (independent of log size)
- **DFG-Based Discovery**: Works directly with DFG structure, not full log
- **Sound Models**: Guarantees sound process models (no deadlocks)
- **Streaming Capable**: Can process logs that don't fit in memory

### Algorithm Overview

IMd is fundamentally different from IMf:

**Traditional IM/IMf**: Work with full log, split log recursively  
**IMd**: Work with DFG only, project DFG recursively

Key Insight: The DFG contains all directly-follows information needed for cut detection, without requiring the full log.

### Scalability Comparison

| Algorithm | Max Events | Max Activities | Memory | Pass Over Log |
|-----------|------------|----------------|--------|---------------|
| Standard IM | 10⁶ | 100 | O(log size) | Multiple |
| IMf | 10⁶ - 10⁷ | 1000 | O(log size) | Multiple |
| **IMd** | **10⁹+** | **10,000** | **O(activities²)** | **Single** |

### DFG-Based Cut Detection

All cut detection uses ONLY the DFG structure:
- Node connectivity
- Edge reachability  
- Start/end node positions
- No trace-level information needed

This enables the algorithm to scale to massive logs.

### Usage

```python
from mining_algorithms.inductive_mining_df import InductiveMiningDF

# Create miner instance
miner = InductiveMiningDF(log)

# Run discovery (pure DFG-based, no edge filtering by default)
miner.generate_graph(
    activity_threshold=0.0,
    traces_threshold=0.0,
    edge_cutoff_threshold=0.0  # Optional: 0.0 = no filtering (canonical)
)

# Get discovered process tree
process_tree = miner.get_graph()
```

### Optional Edge Filtering

IMd includes **optional** edge filtering (not part of core algorithm):

```python
# With optional noise filtering
miner.generate_graph(
    edge_cutoff_threshold=0.1  # Filter edges < 10% of max frequency
)
```

**Note**: For advanced noise handling, use IMf instead.

### Parameter Guidance

| edge_cutoff_threshold | Effect | When to Use |
|----------------------|--------|-------------|
| **0.0** | **No filtering (IMd)** | **Default for pure DFG-based discovery** |
| 0.05-0.1 | Light noise filtering | Very large logs with minor noise |
| 0.1-0.3 | Moderate filtering | Large noisy logs |

### Trade-offs

**Advantages**:
- Extreme scalability (billions of events)
- Single-pass log processing
- Memory efficient (independent of log size)
- Fast execution

**Trade-offs**:
- May lose some trace-level detail
- Less information than full log analysis
- More relaxed validation criteria

### Properties and Guarantees

- **Soundness**: Always produces sound process models
- **Scalability**: Billions of events, thousands of activities
- **Complexity**: O(|events|) for DFG construction, polynomial for discovery
- **Memory**: O(|activities|²) - independent of log size
- **Streaming**: Yes - can process logs that don't fit in memory
- **Recommended for**: Very large logs (> 10⁶ traces) or when memory is constrained

## Comparison of Inductive Mining Variants

| Feature | Standard | Infrequent | Directly-Follows (IMd) |
|---------|----------|------------|------------------------|
| **Primary Goal** | Discover sound process models | Handle noisy logs with adaptive validation | Handle noisy logs with simple filtering |
| **Noise Handling** | Pre-filtering only | Direct DFG filtering + adaptive thresholds | Direct edge frequency filtering |
| **Main Parameter** | Activity/trace thresholds | Noise threshold | Edge threshold |
| **DFG Approach** | Standard DFG | Filtered DFG (removes infrequent edges) | Filtered DFG (simple edge filtering) |
| **Cut Detection** | Single attempt | Two-phase (full then filtered) | Two-phase (filtered then full) |
| **Cut Validation** | Basic validation | Adaptive validation | Basic validation |
| **Fallthrough** | Standard flower model | Standard flower model | Standard flower model |
| **Best Use Case** | Clean, well-structured logs | Complex noise patterns | Simple noise filtering needs |
| **Model Complexity** | Can be high | Reduced through filtering | Reduced through edge filtering |
| **Information Loss** | Minimal (pre-filtering only) | Moderate (edge filtering) | Moderate (edge filtering) |
| **Soundness** | Always sound | Always sound | Always sound |
| **Ease of Use** | Simple (2 parameters) | Medium (3 parameters) | Very Simple (3 parameters, 1 main) |
| **Documentation** | Standard | Good | Excellent (extensive guidance) |

### Choosing the Right Variant

- **Use Standard Inductive Mining when:**
  - Your log is relatively clean and well-structured
  - You want to preserve all behavior in the log
  - Model complexity is not a major concern
  - You have fewer than 20 unique activities

- **Use Inductive Mining Directly-Follows (IMd) when:** ⭐ **Recommended first choice for noisy logs**
  - Your log contains noise or infrequent edges
  - You want a simple, easy-to-configure approach
  - The standard algorithm produces overly complex models
  - You need predictable results with minimal parameter tuning
  - You're new to process mining and want clear guidance

- **Use Inductive Mining Infrequent when:**
  - You need more advanced noise filtering than IMd provides
  - Your log has complex noise patterns requiring adaptive validation
  - IMd doesn't filter enough noise
  - You need sophisticated noise handling capabilities

### Parameter Guidelines

| Variant | Parameter | Range | Recommended Starting Value | Effect of Increasing |
|---------|-----------|-------|---------------------------|---------------------|
| All | activity_threshold | 0.0-1.0 | 0.0 | Removes more activities |
| All | traces_threshold | 0.0-1.0 | 0.2 | Removes more traces |
| Directly-Follows | edge_threshold | 0.0-1.0 | 0.1 | Filters more edges |
| Infrequent | noise_threshold | 0.0-1.0 | 0.2 | Filters more edges adaptively |

### Quick Start Guide

**New to process mining?**
1. Start with **Directly-Follows (IMd)** with `edge_threshold=0.1`
2. If model is too complex, increase to `0.2` or `0.3`
3. If important behavior is missing, decrease to `0.05`

**Experienced user with complex noise?**
- Try **Infrequent** with `noise_threshold=0.2` for advanced adaptive filtering

## References

[1] Leemans, S. J., Fahland, D., & van der Aalst, W. M. (2013). **Discovering block-structured process models from event logs - a constructive approach**. In *International conference on applications and theory of Petri nets and concurrency* (pp. 311-329). Springer, Berlin, Heidelberg.

[2] Leemans, S. J., Fahland, D., & van der Aalst, W. M. (2014). **Discovering block-structured process models from event logs containing infrequent behaviour**. In *International conference on business process management* (pp. 66-78). Springer, Cham.

[3] Leemans, S. J., Fahland, D., & van der Aalst, W. M. (2013). **Discovering block-structured process models from incomplete event logs**. In *International Conference on Applications and Theory of Petri Nets and Concurrency* (pp. 91-110). Springer, Berlin, Heidelberg.

[4] Leemans, S. J. (2017). **Robust process mining with guarantees**. PhD Thesis, Eindhoven University of Technology.

[5] Leemans, S. J., Fahland, D., & van der Aalst, W. M. (2018). **Scalable process discovery and conformance checking**. *Software & Systems Modeling*, 17(2), 599-631.

[6] Leemans, S. J., Fahland, D., & van der Aalst, W. M. (2016). **Exploring processes and deviations**. In *International Conference on Business Process Management* (pp. 304-316). Springer, Cham.

[7] van der Aalst, W. M. (2016). **Process mining: data science in action**. Springer.

[8] Augusto, A., Conforti, R., Dumas, M., La Rosa, M., Maggi, F. M., Marrella, A., ... & Soo, A. (2019). **Automated discovery of process models from event logs: Review and benchmark**. *IEEE transactions on knowledge and data engineering*, 31(4), 686-705.
