from ui.base_algorithm_ui.base_algorithm_view import BaseAlgorithmView
import streamlit as st
from components.number_input_slider import number_input_slider
from components.interactiveGraph import interactiveGraph


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
        st.divider()
        st.markdown("### Common Parameters")
        
        number_input_slider(
            label="Activity Threshold",
            min_value=sidebar_values["activity_threshold"][0],
            max_value=sidebar_values["activity_threshold"][1],
            key="activity_threshold",
            use_columns=False,
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
            use_columns=False,
            help="""Minimum frequency threshold for traces. Traces below this threshold will be filtered out.
            
            **Guidance:**
            - 0.0: Include all traces (may result in overly complex models)
            - 0.1-0.3: Good balance for most logs
            - >0.5: Focus only on very frequent behavior""",
        )

        # Add IMd (Directly-Follows) miner specific controls
        if st.session_state.get('inductive_variant') == "Directly-Follows":
            st.divider()
            st.markdown("### Directly-Follows Miner Settings")
            
            # Display help text for IMd
            with st.expander("ℹ️ About Directly-Follows Miner (IMd)", expanded=False):
                st.markdown("""
                The **Directly-Follows Inductive Miner (IMd)** is a simple and effective variant for handling noisy event logs.

                **Key Features:**
                - **Simple Edge Filtering**: Removes weak directly-follows edges based on frequency
                - **Easy to Configure**: Only one parameter to tune
                - **Well-Documented**: Clear guidance and predictable behavior
                - **Good Balance**: Filters noise while preserving important structure

                **How It Works:**
                Edges with frequency < (max_edge_frequency × edge_threshold) are filtered out.

                **When to Use:**
                - Noisy logs with infrequent behavior
                - You want a simple, easy-to-understand approach
                - Standard miner produces overly complex models
                - You need predictable results with minimal tuning
                
                **Recommended Starting Value:** 0.1 (filters edges below 10% of max frequency)
                """)
            
            # Get current value for dynamic guidance
            current_edge = st.session_state.get("edge_threshold", 0.1)
            
            # Edge threshold with dynamic guidance
            number_input_slider(
                label="Edge Threshold",
                min_value=sidebar_values["edge_threshold"][0],
                max_value=sidebar_values["edge_threshold"][1],
                key="edge_threshold",
                use_columns=False,
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
            st.divider()
            st.markdown("### Infrequent Miner Settings")
            
            # Display enhanced help text for the infrequent miner
            with st.expander("ℹ️ About Infrequent Miner", expanded=False):
                st.markdown("""
                The **Infrequent Inductive Miner** handles noisy event logs by filtering out infrequent directly-follows relations during the mining process.

                **Key Features:**
                - **Noise Filtering**: Removes weak directly-follows edges based on frequency
                - **Hybrid Approach**: First tries full graph, then filtered graph
                - **Adaptive Validation**: Adjusts quality thresholds based on noise level
                - **Connectivity Preservation**: Ensures the graph remains connected after filtering

                **When to Use:**
                - Logs with systematic noise or exceptions
                - When you want to focus on frequent behavior patterns
                - Logs where rare behavior is not important for the process model
                - When standard miner creates overly complex models due to noise
                """)
            
            # Get current noise threshold for dynamic guidance
            current_noise = st.session_state.get("noise_threshold", 0.2)
            
            # Noise threshold with dynamic guidance
            number_input_slider(
                label="Noise Threshold",
                min_value=sidebar_values["noise_threshold"][0],
                max_value=sidebar_values["noise_threshold"][1],
                key="noise_threshold",
                use_columns=False,
                help="""Determines which directly-follows relations are considered noise and filtered out.
                Relations with frequency < threshold × max_relation_frequency will be ignored.
                
                **Guidance:**
                - 0.0: No noise filtering (equivalent to standard miner)
                - 0.1-0.2: Light noise filtering (recommended start)
                - 0.2-0.4: Moderate noise filtering (good for noisy logs)
                - >0.5: Aggressive noise filtering (may lose important behavior)""",
            )
            # Status indicator
            if current_noise == 0.0:
                st.info("🔧 No filtering")
            elif current_noise <= 0.2:
                st.success("✅ Light filtering")
            elif current_noise <= 0.4:
                st.warning("⚠️ Moderate filtering")
            else:
                st.error("🚨 Aggressive filtering")
            
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
            edge_th = st.session_state.get("edge_threshold", 0.1)
            st.markdown(f"**Current Settings:** Edge Threshold: {edge_th:.2f}")
            
        elif current_variant == "Infrequent":
            noise = st.session_state.get("noise_threshold", 0.2)
            st.markdown(f"**Current Settings:** Noise Threshold: {noise:.2f}")

    def display_graph(self, graph) -> None:
        """Override display_graph to include variant-specific key for proper refresh."""
        with self.graph_container:
            if graph is not None:
                # Use variant-specific key to force React component refresh when switching variants
                variant = st.session_state.get('inductive_variant', 'Standard')
                graph_key = f"inductiveGraph_{variant}"
                
                interactiveGraph(
                    graph,
                    onNodeClick=self.display_node_info,
                    height=self.graph_height,
                    key=graph_key
                )