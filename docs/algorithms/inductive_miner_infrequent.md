# Inductive Miner Infrequent

The inductive miner infrequent (IMf) is an extension of the standard inductive miner algorithm, designed to handle noisy event logs. It follows a two-phase cut detection strategy: first attempting to find cuts on the complete directly-follows graph, then filtering infrequent edges and retrying if the first phase fails. This allows the algorithm to discover clean process models even when the log contains noise or infrequent behavior.

The algorithm produces sound process models, meaning every trace can be replayed on the model without deadlocks. It follows the canonical implementation described in the 2014 paper by Leemans et al.

## Two-Phase Cut Detection

The key difference from the standard inductive miner is the two-phase approach to cut detection:

**Phase 1: Full DFG Analysis**
- Attempts to find cuts on the complete directly-follows graph
- Preserves all structural information from the log
- Succeeds when the log is clean or noise doesn't affect structure

**Phase 2: Filtered DFG Analysis**
- Only executed if Phase 1 fails to find a valid cut
- Filters edges with frequency below a calculated threshold
- Retries cut detection on the filtered graph
- Enables discovery in noisy logs by removing infrequent edges

## Noise Filtering

The edge filtering threshold is calculated as:

$$
\text{threshold} = \text{max\_edge\_frequency} \times \text{noise\_threshold}
$$

Where the noise threshold is a parameter between 0.0 and 1.0. Edges with frequency below this threshold are filtered out during Phase 2.

For example, if the maximum edge frequency is 100 and the noise threshold is 0.2, then edges with frequency below 20 are filtered.

## Metrics

The algorithm uses three metrics for filtering:

The activity threshold describes the frequency of an event in relation to the most frequent event. Events with a threshold below this value are removed before mining begins.

The traces threshold describes the frequency of a trace in relation to the most frequent trace. Traces with a threshold below this value are removed before mining begins.

The noise threshold controls the edge filtering during Phase 2. It determines what fraction of the maximum edge frequency is considered "noise" and should be filtered when standard cut detection fails.

## Filtering

Three parameters are used for filtering:

The activity threshold is in the range of 0.0 and 1.0. It removes activities from the log that have a lower relative frequency than this threshold.

The traces threshold is in the range of 0.0 and 1.0. It removes traces from the log that have a lower relative frequency than this threshold.

The noise threshold is in the range of 0.0 and 1.0. The recommended default value is 0.2, which filters edges with frequency below 20% of the maximum edge frequency during Phase 2 cut detection.

[1] Leemans, S. J., Fahland, D., & van der Aalst, W. M. (2014). **Discovering block-structured process models from event logs containing infrequent behaviour**. In *International conference on business process management* (pp. 66-78). Springer, Cham.

[2] Leemans, S. J. (2017). **Robust process mining with guarantees**. PhD Thesis, Eindhoven University of Technology.

[3] van der Aalst, W. M. (2016). **Process mining: data science in action**. Springer.
