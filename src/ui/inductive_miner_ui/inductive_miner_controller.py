from ui.base_algorithm_ui.base_algorithm_controller import BaseAlgorithmController
from ui.inductive_miner_ui.inductive_miner_view import InductiveMinerView
from mining_algorithms.inductive_mining import InductiveMining
from mining_algorithms.inductive_mining_infrequent import InductiveMiningInfrequent
from mining_algorithms.inductive_mining_approximate import InductiveMiningApproximate
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
            
        # Initialize approximate miner specific parameters
        if "simplification_threshold" not in st.session_state:
            st.session_state.simplification_threshold = 0.1
            
        if "min_bin_freq" not in st.session_state:
            st.session_state.min_bin_freq = 0.2
            
        # Initialize infrequent miner specific parameters
        if "noise_threshold" not in st.session_state:
            st.session_state.noise_threshold = 0.2
            
        # Map of variant names to their class implementations
        self.variant_classes = {
            "Standard": InductiveMining,
            "Infrequent": InductiveMiningInfrequent,
            "Approximate": InductiveMiningApproximate
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
            
        # Handle approximate miner parameters
        if isinstance(self.mining_model, InductiveMiningApproximate):
            if "simplification_threshold" not in st.session_state:
                st.session_state.simplification_threshold = getattr(
                    self.mining_model, "simplification_threshold", 0.1
                )
            if "min_bin_freq" not in st.session_state:
                st.session_state.min_bin_freq = getattr(
                    self.mining_model, "min_bin_freq", 0.2
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
        self.simplification_threshold = st.session_state.simplification_threshold
        self.min_bin_freq = st.session_state.min_bin_freq
        self.noise_threshold = st.session_state.noise_threshold

    def perform_mining(self) -> None:
        """Performs the mining of the Inductive Miner algorithm."""
        # Check if we need to switch the mining model class based on selected variant
        variant_class = self.variant_classes[self.selected_variant]
        if not isinstance(self.mining_model, variant_class):
            # Create a new instance of the selected variant class
            self.mining_model = variant_class(self.mining_model.log)
        
        # Validate parameters
        self.activity_threshold = max(0.0, min(1.0, self.activity_threshold))
        self.traces_threshold = max(0.0, min(1.0, self.traces_threshold))
        
        # Call generate_graph with appropriate parameters based on variant
        if self.selected_variant == "Approximate":
            # Validate approximate miner specific parameters
            self.simplification_threshold = max(0.0, min(0.9, self.simplification_threshold))
            self.min_bin_freq = max(0.0, min(0.9, self.min_bin_freq))
            
            self.mining_model.generate_graph(
                self.activity_threshold, 
                self.traces_threshold,
                simplification_threshold=self.simplification_threshold,
                min_bin_freq=self.min_bin_freq
            )
        elif self.selected_variant == "Infrequent":
            # Validate infrequent miner specific parameters
            self.noise_threshold = max(0.0, min(0.9, self.noise_threshold))
            
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
        # Check basic parameters
        basic_params_changed = (
            self.mining_model.get_activity_threshold() != self.activity_threshold
            or self.mining_model.get_traces_threshold() != self.traces_threshold
            or not isinstance(self.mining_model, self.variant_classes[self.selected_variant])
        )
        
        # Check approximate miner parameters if applicable
        if self.selected_variant == "Approximate" and isinstance(self.mining_model, InductiveMiningApproximate):
            approx_params_changed = (
                getattr(self.mining_model, "simplification_threshold", 0.1) != self.simplification_threshold
                or getattr(self.mining_model, "min_bin_freq", 0.2) != self.min_bin_freq
            )
            return basic_params_changed or approx_params_changed
            
        # Check infrequent miner parameters if applicable
        if self.selected_variant == "Infrequent" and isinstance(self.mining_model, InductiveMiningInfrequent):
            infrequent_params_changed = (
                getattr(self.mining_model, "noise_threshold", 0.2) != self.noise_threshold
            )
            return basic_params_changed or infrequent_params_changed
            
        return basic_params_changed

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
            "simplification_threshold": (0.0, 0.9),
            "min_bin_freq": (0.0, 0.9),
            "noise_threshold": (0.0, 0.9),
        }

        return sidebar_values
