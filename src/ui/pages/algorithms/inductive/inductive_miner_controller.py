from ui.pages.algorithms.base_algorithm_controller import BaseAlgorithmController
from ui.pages.algorithms.inductive.inductive_miner_view import InductiveMinerView
from core.algorithms.inductive import InductiveMining
from core.algorithms.inductive_infrequent import InductiveMiningInfrequent
import streamlit as st


class InductiveMinerController(BaseAlgorithmController):
    """Controller for the Inductive Miner algorithm."""

    def __init__(
        self, views=None, mining_model_class=None, dataframe_transformations=None
    ):
        """Initializes the controller for the Inductive Miner algorithm.

        Parameters
        ----------
        views : List[BaseAlgorithmView] | BaseAlgorithmView, optional
            The views for the Inductive Miner algorithm. If None is passed, the default view is used, by default None
        mining_model_class : MiningInterface Class, optional
            The mining model class for the Inductive Miner algorithm. If None is passed, the default model class is used, by default None
        dataframe_transformations : DataframeTransformations, optional
            The class for the dataframe transformations. If None is passed, a new instance is created, by default None
        """
        if views is None:
            views = [InductiveMinerView()]

        if mining_model_class is None:
            mining_model_class = InductiveMining
        super().__init__(views, mining_model_class, dataframe_transformations)
        
        # Initialize variant to Standard if not set
        if "inductive_variant" not in st.session_state:
            st.session_state.inductive_variant = "Standard"
            
        # Initialize infrequent miner specific parameters
        if "noise_threshold" not in st.session_state:
            st.session_state.noise_threshold = 0.2
            
        # Map of variant names to their class implementations
        self.variant_classes = {
            "Standard": InductiveMining,
            "Infrequent": InductiveMiningInfrequent,
        }

    def get_page_title(self) -> str:
        """Returns the page title.

        Returns
        -------
        str
            The page title.
        """
        return "Inductive Mining"

    def process_algorithm_parameters(self):
        """Processes the algorithm parameters from the session state. The parameters are set to the instance variables.
        If the parameters are not set in the session state, the default values are used.
        """
        # set session state from instance variables if not set
        if "traces_threshold" not in st.session_state:
            st.session_state.traces_threshold = self.mining_model.get_traces_threshold()

        if "activity_threshold" not in st.session_state:
            st.session_state.activity_threshold = (
                self.mining_model.get_activity_threshold()
            )
                
        # Handle infrequent miner parameters
        if isinstance(self.mining_model, InductiveMiningInfrequent):
            if "noise_threshold" not in st.session_state:
                st.session_state.noise_threshold = getattr(
                    self.mining_model, "noise_threshold", 0.2
                )

        # set instance variables from session state
        self.traces_threshold = st.session_state.traces_threshold
        self.activity_threshold = st.session_state.activity_threshold
        self.selected_variant = st.session_state.inductive_variant
        self.noise_threshold = st.session_state.noise_threshold

    def perform_mining(self) -> None:
        """Performs the mining of the Inductive Miner algorithm."""
        # Check if we need to switch the mining model class based on selected variant
        variant_class = self.variant_classes[self.selected_variant]
        if not isinstance(self.mining_model, variant_class):
            # Create a new instance of the selected variant class
            self.mining_model = variant_class(self.mining_model.log)
            
            # CRITICAL: Update session state with the new model instance
            # This ensures the new model persists across Streamlit reruns
            st.session_state.model = self.mining_model
            
            # Clear any cached results when switching variants to prevent stale visualizations
            if hasattr(self.mining_model, '_dfg_cache'):
                self.mining_model._dfg_cache.clear()
            if hasattr(self.mining_model, '_binning_cache'):
                self.mining_model._binning_cache.clear()
            if hasattr(self.mining_model, '_edge_freq_cache'):
                self.mining_model._edge_freq_cache.clear()
                
            # Force a fresh computation by clearing any existing graph and results
            self.mining_model.graph = None
            if hasattr(self.mining_model, 'process_tree'):
                self.mining_model.process_tree = None
            if hasattr(self.mining_model, 'filtered_log'):
                self.mining_model.filtered_log = None
                
            # Also clear any cached node sizes or frequency maps that might affect visualization
            if hasattr(self.mining_model, 'node_sizes'):
                self.mining_model.node_sizes = {}
            if hasattr(self.mining_model, '_frequency_map'):
                self.mining_model._frequency_map = None
        
        # Validate parameters
        self.activity_threshold = max(0.0, min(1.0, self.activity_threshold))
        self.traces_threshold = max(0.0, min(1.0, self.traces_threshold))
        
        # Call generate_graph with appropriate parameters based on variant
        if self.selected_variant == "Infrequent":
            # Validate infrequent miner specific parameters
            self.noise_threshold = max(0.0, min(0.9, self.noise_threshold))
            
            # Ensure the mining model has the correct parameters before generation
            if hasattr(self.mining_model, 'noise_threshold'):
                self.mining_model.noise_threshold = self.noise_threshold
            
            self.mining_model.generate_graph(
                self.activity_threshold, 
                self.traces_threshold,
                noise_threshold=self.noise_threshold
            )
        else:
            self.mining_model.generate_graph(self.activity_threshold, self.traces_threshold)

    def have_parameters_changed(self) -> bool:
        """Checks if the algorithm parameters have changed.

        Returns
        -------
        bool
            True if the algorithm parameters have changed, False otherwise.
        """
        # Always check for variant mismatch first - this forces re-computation when switching
        variant_mismatch = not isinstance(self.mining_model, self.variant_classes[self.selected_variant])
        
        # Log variant switching for debugging if needed
        # if variant_mismatch:
        #     current_type = type(self.mining_model).__name__
        #     expected_type = self.variant_classes[self.selected_variant].__name__
        #     self.logger.debug(f"Variant switch detected: {current_type} → {expected_type}")
        
        # Check basic parameters (always apply to all variants)
        basic_params_changed = (
            self.mining_model.get_activity_threshold() != self.activity_threshold
            or self.mining_model.get_traces_threshold() != self.traces_threshold
            or variant_mismatch
        )
        
        # Check variant-specific parameters
        variant_params_changed = False
                
        # Check infrequent miner parameters if selected
        if self.selected_variant == "Infrequent":
            if isinstance(self.mining_model, InductiveMiningInfrequent):
                old_noise = getattr(self.mining_model, "noise_threshold", 0.2)
                variant_params_changed = (old_noise != self.noise_threshold)
                if variant_params_changed:
                    self.logger.info(f"Noise threshold changed: {old_noise} → {self.noise_threshold}")
            else:
                # Model type doesn't match selected variant - force change
                variant_params_changed = True
            
        return basic_params_changed or variant_params_changed

    def get_sidebar_values(self) -> dict[str, tuple[int | float, int | float]]:
        """Returns the sidebar values for the Inductive Miner algorithm.

        Returns
        -------
        dict[str, tuple[int | float, int | float]]
            A dictionary containing the minimum and maximum values for the sidebar sliders.
            The keys of the dictionary are equal to the keys of the sliders.
        """
        sidebar_values = {
            "traces_threshold": (0.0, 1.0),
            "activity_threshold": (0.0, 1.0),
            "noise_threshold": (0.0, 0.9),
        }

        return sidebar_values
