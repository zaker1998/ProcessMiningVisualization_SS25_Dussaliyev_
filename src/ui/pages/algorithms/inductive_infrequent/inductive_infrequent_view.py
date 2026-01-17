from ui.pages.algorithms.base_algorithm_view import BaseAlgorithmView
import streamlit as st
from ui.components.inputs import number_input_slider
from ui.components.interactive_graph import interactiveGraph


class InductiveInfrequentView(BaseAlgorithmView):
    """View for the Inductive Miner - Infrequent algorithm."""

    def render_sidebar(
        self, sidebar_values: dict[str, tuple[int | float, int | float]]
    ) -> None:
        """Renders the sidebar for the Inductive Miner - Infrequent algorithm.

        Parameters
        ----------
        sidebar_values : dict[str, tuple[int | float, int | float]]
            A dictionary containing the minimum and maximum values for the sidebar sliders.
            The keys of the dictionary are equal to the keys of the sliders.
        """
        st.markdown("### Inductive Miner - Infrequent")
        st.caption("Noise-tolerant inductive mining for process discovery")
        
        # Common parameters section
        st.markdown("#### Filtering Parameters")
        
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
        
        # Noise filtering section
        st.markdown("#### Noise Filtering")
        
        # Get current noise threshold for dynamic guidance
        current_noise = st.session_state.get("noise_threshold", 0.2)
        
        number_input_slider(
            label="Noise Threshold",
            min_value=sidebar_values["noise_threshold"][0],
            max_value=sidebar_values["noise_threshold"][1],
            key="noise_threshold",
            help="""Determines which directly-follows relations are considered noise and filtered out.
            Relations with frequency < threshold × max_relation_frequency will be ignored.
            
            **Guidance:**
            - 0.0: No noise filtering (equivalent to standard miner)
            - 0.1-0.2: Light noise filtering (recommended start)
            - 0.2-0.4: Moderate noise filtering (good for noisy logs)
            - >0.5: Aggressive noise filtering (may lose important behavior)""",
        )
        
        # Noise threshold guidance
        st.markdown("**💡 Noise Threshold Tips:**")
        if current_noise == 0.0:
            st.info("ℹ️ No noise filtering - equivalent to standard inductive miner")
        elif current_noise <= 0.3:
            st.success("✅ Good for handling systematic noise while preserving structure")
        elif current_noise <= 0.5:
            st.warning("⚠️ May filter out some important but infrequent behavior")
        else:
            st.error("🚨 Very aggressive - only the most frequent patterns will remain")
            
        # Add helpful tips
        with st.expander("💡 Algorithm Tips"):
            st.markdown("""
            **Inductive Miner - Infrequent (IMf)** is designed to handle noisy event logs.
            
            - **Noise Threshold** filters infrequent directly-follows relations before cut detection
            - The algorithm uses a two-phase approach for better noise handling
            - Based on Leemans et al. (2014) research paper
            
            **When to use IMf:**
            - Your event log contains recording errors or incomplete traces
            - You want to focus on the main process flow, ignoring exceptions
            - Standard Inductive Miner produces overly complex models
            """)

    def render_main_panel(self) -> None:
        """Render the main panel content."""
        st.markdown("### 🔍 Inductive Miner - Infrequent")
        
        # Show parameter summary
        noise = st.session_state.get("noise_threshold", 0.2)
        activity = st.session_state.get("activity_threshold", 0.0)
        traces = st.session_state.get("traces_threshold", 0.0)
        
        st.markdown(f"**Current Settings:** Noise: {noise:.2f} | Activity: {activity:.2f} | Traces: {traces:.2f}")

    def display_graph(self, graph) -> None:
        """Display the process model graph with appropriate key for refresh."""
        with self.graph_container:
            if graph is not None:
                # Include all threshold values in the key to ensure refresh when any parameter changes
                activity_threshold = st.session_state.get('activity_threshold', 0.0)
                traces_threshold = st.session_state.get('traces_threshold', 0.0)
                noise_threshold = st.session_state.get('noise_threshold', 0.2)
                
                # Create a unique key that includes all threshold values
                graph_key = (
                    f"inductiveInfrequentGraph_"
                    f"act{activity_threshold:.3f}_"
                    f"trc{traces_threshold:.3f}_"
                    f"noi{noise_threshold:.3f}"
                )
                
                interactiveGraph(
                    graph,
                    onNodeClick=self.display_node_info,
                    height=self.graph_height,
                    key=graph_key
                )
