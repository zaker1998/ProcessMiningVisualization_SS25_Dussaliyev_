from ui.pages.algorithms.base_algorithm_view import BaseAlgorithmView
import streamlit as st
from ui.components.inputs import number_input_slider
from ui.components.interactive_graph import interactiveGraph


class InductiveMinerView(BaseAlgorithmView):
    """View for the Inductive Miner algorithm."""

    def render_sidebar(
        self, sidebar_values: dict[str, tuple[int | float, int | float]]
    ) -> None:
        """Renders the sidebar for the Inductive Miner algorithm.

        Parameters
        ----------
        sidebar_values : dict[str, tuple[int | float, int | float]]
            A dictionary containing the minimum and maximum values for the sidebar sliders.
            The keys of the dictionary are equal to the keys of the sliders.
        """
        st.markdown("### Inductive Miner")
        st.caption("Classic algorithm for well-structured process discovery")
        
        number_input_slider(
            label="Activity Threshold",
            min_value=sidebar_values["activity_threshold"][0],
            max_value=sidebar_values["activity_threshold"][1],
            key="activity_threshold",
            help="""Minimum frequency threshold for activities. Activities below this threshold will be filtered out.
            
            **Guidance:**
            - 0.0: Include all activities (recommended for most cases)
            - 0.1-0.2: Filter very rare activities
            - >0.3: Aggressive filtering (may lose important behavior)""",
        )

        number_input_slider(
            label="Traces Threshold",
            min_value=sidebar_values["traces_threshold"][0],
            max_value=sidebar_values["traces_threshold"][1],
            key="traces_threshold",
            help="""Minimum frequency threshold for traces. Traces below this threshold will be filtered out.
            
            **Guidance:**
            - 0.0: Include all traces (may result in overly complex models)
            - 0.1-0.3: Good balance for most logs
            - >0.5: Focus only on very frequent behavior""",
        )
        
        # Add helpful tips
        with st.expander("💡 Algorithm Tips"):
            st.markdown("""
            **Inductive Miner** discovers process models by recursively splitting the event log.
            
            - Guarantees sound process models
            - Good for well-structured, clean event logs
            - For noisy logs, try **Inductive Miner - Infrequent** instead
            
            **When to use:**
            - Your event log is clean and well-structured
            - You need a sound process model
            - You want to understand the main control flow
            """)

    def render_main_panel(self) -> None:
        """Render the main panel content."""
        st.markdown("### 🔧 Inductive Miner")
        
        # Show parameter summary
        activity = st.session_state.get("activity_threshold", 0.0)
        traces = st.session_state.get("traces_threshold", 0.0)
        
        st.markdown(f"**Current Settings:** Activity: {activity:.2f} | Traces: {traces:.2f}")

    def display_graph(self, graph) -> None:
        """Display the process model graph with appropriate key for refresh."""
        with self.graph_container:
            if graph is not None:
                # Include all threshold values in the key to ensure refresh when any parameter changes
                activity_threshold = st.session_state.get('activity_threshold', 0.0)
                traces_threshold = st.session_state.get('traces_threshold', 0.0)
                
                # Create a unique key that includes all threshold values
                graph_key = (
                    f"inductiveGraph_"
                    f"act{activity_threshold:.3f}_"
                    f"trc{traces_threshold:.3f}"
                )
                
                interactiveGraph(
                    graph,
                    onNodeClick=self.display_node_info,
                    height=self.graph_height,
                    key=graph_key
                )