from ui.pages.algorithms.base_algorithm_view import BaseAlgorithmView
import streamlit as st
from ui.components.inputs import number_input_slider
from ui.components.interactive_graph import interactiveGraph


class InductiveMinerView(BaseAlgorithmView):
    """View for the Inductive Miner algorithm."""

    def render_sidebar(
        self, sidebar_values: dict[str, tuple[int | float, int | float]]
    ) -> None:
        
        # Variant selection
        st.markdown("### Algorithm Variant")
        variant_options = ["Standard", "Directly-Follows", "Infrequent"]
        selected_variant = st.selectbox(
            "Select Inductive Miner variant:",
            variant_options,
            key="inductive_variant",
            help="""
            **Standard**: Classic inductive miner for well-structured logs
            **Directly-Follows**: Simple edge filtering for cleaner models (recommended for noisy logs)
            **Infrequent**: Advanced noise filtering with adaptive thresholds
            """
        )
        
        # Common parameters
        st.markdown("### Common Parameters")
        
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

        # Add IMd (Directly-Follows) miner specific controls
        if st.session_state.get('inductive_variant') == "Directly-Follows":
            st.markdown("### Directly-Follows Miner Settings")
            
            # Get current value for dynamic guidance
            current_edge = st.session_state.get("edge_threshold", 0.0)
            
            # Edge threshold with dynamic guidance
            number_input_slider(
                label="Edge Threshold",
                min_value=sidebar_values["edge_threshold"][0],
                max_value=sidebar_values["edge_threshold"][1],
                key="edge_threshold",
                help="""Controls filtering of weak directly-follows edges.
                
                **Formula:** threshold_freq = max_edge_freq × edge_threshold
                
                **Guidance:**
                - 0.0: No filtering (equivalent to standard miner)
                - 0.05-0.1: Light filtering (recommended for most cases)
                - 0.1-0.3: Moderate filtering (good for noisy logs)
                - >0.3: Aggressive filtering (may lose important behavior)
                
                **Example:** If edge_threshold=0.1 and max edge has frequency 100,
                then only edges with frequency ≥ 10 are kept.""",
            )
            
            # Status indicator with clear guidance
            if current_edge == 0.0:
                st.info("🔧 **No filtering** - Equivalent to standard miner")
            elif current_edge <= 0.1:
                st.success("✅ **Light filtering** - Recommended for most logs")
            elif current_edge <= 0.3:
                st.warning("⚠️ **Moderate filtering** - Good for noisy logs")
            else:
                st.error("🚨 **Aggressive filtering** - May lose important behavior")
            
        # Add Infrequent miner specific controls that only show when the variant is Infrequent
        if st.session_state.get('inductive_variant') == "Infrequent":
            st.markdown("### Infrequent Miner Settings")
            
            # Get current noise threshold for dynamic guidance
            current_noise = st.session_state.get("noise_threshold", 0.2)
            
            # Noise threshold with dynamic guidance
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

        # Add general tips section
       

    def render_main_panel(self) -> None:
        """Render the main panel content."""
        # Display current variant information
        current_variant = st.session_state.get('inductive_variant', 'Standard')
        
        variant_descriptions = {
            "Standard": "🔧 **Standard Inductive Miner** - Classic algorithm for well-structured logs",
            "Directly-Follows": "🎯 **Directly-Follows Miner (IMd)** - Simple edge filtering for cleaner models", 
            "Infrequent": "🔍 **Infrequent Inductive Miner** - Advanced noise filtering for complex logs"
        }
        
        st.markdown(f"### {variant_descriptions.get(current_variant, 'Unknown Variant')}")
        
        # Show parameter summary for non-standard variants
        if current_variant == "Directly-Follows":
            edge_th = st.session_state.get("edge_threshold", 0.0)
            st.markdown(f"**Current Settings:** Edge Threshold: {edge_th:.2f}")
            
        elif current_variant == "Infrequent":
            noise = st.session_state.get("noise_threshold", 0.2)
            st.markdown(f"**Current Settings:** Noise Threshold: {noise:.2f}")

    def display_graph(self, graph) -> None:
        """Override display_graph to include variant-specific key for proper refresh."""
        with self.graph_container:
            if graph is not None:
                # Use variant-specific key PLUS all threshold values to force React component refresh
                # when either the variant OR any threshold changes
                variant = st.session_state.get('inductive_variant', 'Standard')
                
                # Include ALL threshold values in the key to ensure refresh when ANY threshold changes
                activity_threshold = st.session_state.get('activity_threshold', 0.0)
                traces_threshold = st.session_state.get('traces_threshold', 0.0)
                edge_threshold = st.session_state.get('edge_threshold', 0.1)
                noise_threshold = st.session_state.get('noise_threshold', 0.2)
                
                # Create a unique key that includes variant and all threshold values
                # This ensures the React component re-renders whenever ANY parameter changes
                graph_key = (
                    f"inductiveGraph_{variant}_"
                    f"act{activity_threshold:.3f}_"
                    f"trc{traces_threshold:.3f}_"
                    f"edg{edge_threshold:.3f}_"
                    f"noi{noise_threshold:.3f}"
                )
                
                interactiveGraph(
                    graph,
                    onNodeClick=self.display_node_info,
                    height=self.graph_height,
                    key=graph_key
                )