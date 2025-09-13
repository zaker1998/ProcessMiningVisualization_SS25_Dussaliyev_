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
        variant_options = ["Standard", "Approximate", "Infrequent"]
        selected_variant = st.selectbox(
            "Select Inductive Miner variant:",
            variant_options,
            key="inductive_variant",
            help="""
            **Standard**: Classic inductive miner for well-structured logs
            **Approximate**: Uses simplification and activity binning for complex/noisy logs  
            **Infrequent**: Filters out low-frequency behavior to handle noise
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

        # Add Approximate miner specific controls that only show when the variant is Approximate
        if st.session_state.get('inductive_variant') == "Approximate":
            st.divider()
            st.markdown("### Approximate Miner Settings")
            
            # Display enhanced help text for the approximate miner
            with st.expander("ℹ️ About Approximate Miner", expanded=False):
                st.markdown("""
                The **Approximate Inductive Miner** is designed for complex, noisy, or large event logs where the standard algorithm might produce overly complicated models.

                **Key Features:**
                - **Activity Binning**: Groups similar activities together to reduce model complexity
                - **DFG Simplification**: Removes weak directly-follows relations 
                - **Cut Quality Validation**: Ensures decompositions are meaningful
                - **Auto-Parameter Tuning**: Tries different parameter combinations automatically

                **When to Use:**
                - Large logs with many unique activities (>50)
                - Noisy logs with irregular behavior
                - When standard miner produces flower models
                - When you need more generalized process models
                """)
            
            # Get current values for dynamic guidance
            current_simpl = st.session_state.get("simplification_threshold", 0.1)
            current_bin = st.session_state.get("min_bin_freq", 0.2)
            
            # Simplification threshold with dynamic guidance
            number_input_slider(
                label="Simplification Threshold",
                min_value=sidebar_values["simplification_threshold"][0],
                max_value=sidebar_values["simplification_threshold"][1],
                key="simplification_threshold",
                use_columns=False,
                help="""Controls how aggressively the directly-follows graph is simplified by removing weak edges.
                
                **Guidance:**
                - 0.0: No simplification (use full graph)
                - 0.05-0.1: Light simplification (recommended start)
                - 0.1-0.2: Moderate simplification
                - >0.3: Aggressive simplification (may lose important structure)""",
            )
            # Status indicator
            if current_simpl == 0.0:
                st.info("🔧 No simplification")
            elif current_simpl <= 0.1:
                st.success("✅ Light simplification")
            elif current_simpl <= 0.2:
                st.warning("⚠️ Moderate simplification")
            else:
                st.error("🚨 Aggressive simplification")
            
            # Min behavior frequency with dynamic guidance
            number_input_slider(
                label="Min. Behavior Frequency",
                min_value=sidebar_values["min_bin_freq"][0],
                max_value=sidebar_values["min_bin_freq"][1],
                key="min_bin_freq",
                use_columns=False,
                help="""Minimum frequency for grouping activities with similar behavior patterns.
                
                **Guidance:**
                - 0.0: No activity binning
                - 0.1-0.2: Light binning (group very similar activities)
                - 0.2-0.4: Moderate binning (recommended for noisy logs)
                - >0.5: Aggressive binning (may over-generalize)""",
            )
            # Status indicator
            if current_bin == 0.0:
                st.info("🔧 No binning")
            elif current_bin <= 0.2:
                st.success("✅ Light binning")
            elif current_bin <= 0.4:
                st.warning("⚠️ Moderate binning")
            else:
                st.error("🚨 Aggressive binning")
            
            # Parameter combination guidance
            if current_simpl > 0.0 or current_bin > 0.0:
                st.markdown("**💡 Parameter Combination Tips:**")
                if current_simpl > 0.2 and current_bin > 0.3:
                    st.warning("⚠️ Both parameters are high - may result in over-simplified models")
                elif current_simpl == 0.0 and current_bin == 0.0:
                    st.info("ℹ️ No approximation active - equivalent to standard miner")
                else:
                    st.success("✅ Good parameter balance for approximation")
            
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
        st.divider()
        with st.expander("🎯 General Mining Tips", expanded=False):
            st.markdown("""
            **Choosing the Right Variant:**
            
            **Use Standard** when:
            - Log is clean and well-structured
            - You want the most precise model
            - Log size is manageable (<1000 traces)
            
            **Use Approximate** when:
            - Log has many unique activities (>50)
            - You need a more generalized model
            - Standard miner produces flower models
            - Log contains complex concurrent behavior
            
            **Use Infrequent** when:
            - Log contains systematic noise
            - You want to focus on frequent patterns only
            - Exceptional behavior should be ignored
            - Log has clear main process with deviations
            
            **Parameter Tuning Strategy:**
            1. Start with default values
            2. Increase thresholds gradually if model is too complex
            3. Decrease thresholds if important behavior is missing
            4. Use the guidance indicators to avoid extreme settings
            """)

    def render_main_panel(self) -> None:
        """Render the main panel content."""
        # Display current variant information
        current_variant = st.session_state.get('inductive_variant', 'Standard')
        
        variant_descriptions = {
            "Standard": "🔧 **Standard Inductive Miner** - Classic algorithm for well-structured logs",
            "Approximate": "🎯 **Approximate Inductive Miner** - Simplification and binning for complex logs", 
            "Infrequent": "🔍 **Infrequent Inductive Miner** - Noise filtering for cleaner models"
        }
        
        st.markdown(f"### {variant_descriptions.get(current_variant, 'Unknown Variant')}")
        
        # Show parameter summary for non-standard variants
        if current_variant == "Approximate":
            simpl = st.session_state.get("simplification_threshold", 0.1)
            bin_freq = st.session_state.get("min_bin_freq", 0.2)
            st.markdown(f"**Current Settings:** Simplification: {simpl:.2f}, Binning: {bin_freq:.2f}")
            
        elif current_variant == "Infrequent":
            noise = st.session_state.get("noise_threshold", 0.2)
            st.markdown(f"**Current Settings:** Noise Threshold: {noise:.2f}")
        
        # Call parent implementation for the rest
        super().render_main_panel()

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