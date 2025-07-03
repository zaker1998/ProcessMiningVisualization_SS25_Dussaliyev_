from ui.base_algorithm_ui.base_algorithm_view import BaseAlgorithmView
import streamlit as st
from components.number_input_slider import number_input_slider


class InductiveMinerView(BaseAlgorithmView):
    """View for the Inductive Miner algorithm."""

    def render_sidebar(
        self, sidebar_values: dict[str, tuple[int | float, int | float]]
    ) -> None:
        """Renders the sidebar for the Inductive Miner algorithm.

        Parameters
        ----------
        sidebar_values : dict[str, tuple[int  |  float, int  |  float]]
            A dictionary containing the minimum and maximum values for the sidebar sliders.
            The keys of the dictionary are equal to the keys of the sliders.
        """
        # Add a container with custom styling for consistent appearance in both themes
        with st.container():
            st.markdown("### Mining Variant")
            
            # Use selectbox with descriptive label and help text
            variant_options = ["Standard", "Infrequent", "Approximate"]
            variant_help = """
            Select the Inductive Mining variant to use:
            - **Standard**: Classic inductive miner
            - **Infrequent**: Inductive miner with infrequent behavior handling
            - **Approximate**: Approximate inductive miner that provides a balance between precision and generalization
            """
            
            st.selectbox(
                "Select variant",
                options=variant_options,
                key="inductive_variant",
                help=variant_help
            )
            
            # Add spacing between controls
            st.divider()
        
        # Threshold controls with improved styling
        st.markdown("### Threshold Settings")
        
        number_input_slider(
            label="Traces Threshold",
            min_value=sidebar_values["traces_threshold"][0],
            max_value=sidebar_values["traces_threshold"][1],
            key="traces_threshold",
            help="""The traces threshold parameter determines the minimum frequency of a trace to be included in the graph. 
            All traces with a frequency that is lower than treshold * max_trace_frequency will be removed. The higher the value, the less traces will be included in the graph.""",
        )

        number_input_slider(
            label="Activity Threshold",
            min_value=sidebar_values["activity_threshold"][0],
            max_value=sidebar_values["activity_threshold"][1],
            key="activity_threshold",
            help="""The activity threshold parameter determines the minimum frequency of an activity to be included in the graph. 
            All activities with a frequency that is lower than treshold * max_event_frequency will be removed.
            The higher the value, the less activities will be included in the graph.""",
        )

        # Add Approximate miner specific controls that only show when the variant is Approximate
        if st.session_state.get('inductive_variant') == "Approximate":
            st.divider()
            st.markdown("### Approximate Miner Settings")
            
            # Display help text for the approximate miner
            st.info("""
            The Approximate Inductive Miner uses simplification strategies to handle complex or noisy logs.
            It can:
            - Group similar activities
            - Simplify the directly-follows graph
            - Handle recursive structures better
            - Create more generalized models
            
            Adjust the parameters below to control how aggressively the algorithm simplifies the model.
            """)
            
            number_input_slider(
                label="Simplification Threshold",
                min_value=sidebar_values["simplification_threshold"][0],
                max_value=sidebar_values["simplification_threshold"][1],
                key="simplification_threshold",
                help="""The simplification threshold determines how aggressively the miner simplifies directly-follows relations. 
                Higher values result in simpler models but may lose precision. A value of 0.0 means no simplification.""",
            )
            
            number_input_slider(
                label="Min. Behavior Frequency",
                min_value=sidebar_values["min_bin_freq"][0],
                max_value=sidebar_values["min_bin_freq"][1],
                key="min_bin_freq",
                help="""Minimum frequency for binning activities with similar behavior.
                Higher values will group more activities together, resulting in a simpler model.""",
            )
            
        # Add Infrequent miner specific controls that only show when the variant is Infrequent
        if st.session_state.get('inductive_variant') == "Infrequent":
            st.divider()
            st.markdown("### Infrequent Miner Settings")
            
            # Display help text for the infrequent miner
            st.info("""
            The Infrequent Inductive Miner filters infrequent directly-follows relations during cut detection.
            This helps to:
            - Handle noisy logs better
            - Focus on frequent behavior patterns
            - Reduce overfitting to rare behaviors
            - Create more generalizable models
            
            The noise threshold determines which directly-follows relations are considered noise and should be filtered out.
            """)
            
            number_input_slider(
                label="Noise Threshold",
                min_value=sidebar_values["noise_threshold"][0],
                max_value=sidebar_values["noise_threshold"][1],
                key="noise_threshold",
                help="""The noise threshold determines which directly-follows relations are filtered out during cut detection.
                Relations with frequency lower than threshold * max_relation_frequency will be ignored.
                Higher values result in more aggressive noise filtering.""",
            )