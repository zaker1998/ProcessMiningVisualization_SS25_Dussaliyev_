import streamlit as st

class ColumnSelectionView:
    def show_algorithm_selector(self):
        """Shows the algorithm selector for the user to choose which mining algorithm to use."""
        st.header("Select Mining Algorithm")
        
        algorithm_options = {
            "Inductive Miner": "inductive_miner",
            "Inductive Miner Infrequent": "inductive_miner_infrequent",
            "Approximate Inductive Miner": "approximate_inductive_miner",
            # You can add other algorithms here as they're implemented
        }
        
        selected_algorithm = st.selectbox(
            "Mining Algorithm",
            options=list(algorithm_options.keys()),
            index=0,
            help="Select which process mining algorithm to use"
        )
        
        # Store the selected algorithm in session state
        st.session_state.selected_algorithm = algorithm_options[selected_algorithm]
        
        # Show algorithm-specific documentation if available
        if selected_algorithm == "Inductive Miner":
            st.info("""
            The basic Inductive Miner discovers process models based on directly-follows relations.
            It produces sound process models that can replay every trace from the input log.
            """)
        elif selected_algorithm == "Inductive Miner Infrequent":
            st.info("""
            The Inductive Miner Infrequent extends the basic algorithm by filtering out infrequent behavior
            during the mining process using a noise threshold. This makes it more robust to noise
            and produces simpler models.
            """)
        elif selected_algorithm == "Approximate Inductive Miner":
            st.info("""
            The Approximate Inductive Miner improves performance on large logs by sampling.
            It can process much larger event logs with reduced computational cost
            while maintaining good model quality.
            """)