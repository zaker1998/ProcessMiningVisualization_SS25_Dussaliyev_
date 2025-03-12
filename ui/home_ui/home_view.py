import streamlit as st
from ui.base_ui.base_view import BaseView
from config import algorithm_mappings
from components.buttons import navigation_button


class HomeView(BaseView):
    """View for the Home page."""

    def create_layout(self):
        """Creates the layout for the Home page."""
        super().create_layout()
        _, self.content_column, _ = st.columns([1, 6, 1])

    def display_intro(self):
        """Displays the introduction text for the Home page."""
        # Custom CSS to reduce margins
        st.markdown("""
    <style>
        .block-container {
            padding-top: 0rem;
            padding-bottom: 1rem;
        }

        /* Target only the h1 within block-container */
        .block-container h1 {
            padding-top: 0.5rem !important;
            padding-bottom: 1rem !important;
        }
    </style>
""", unsafe_allow_html=True)

        with self.content_column:
            st.title("🚀 Process Mining Visualization")
            
            # Feature highlights in a grid
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### 📊 Key Features
                - Intuitive process log visualization
                - Multiple mining algorithms
                - Interactive dependency graphs
                - Easy data import/export
                """)
                
            with col2:
                st.markdown("""
                ### 🎯 Getting Started
                1. Upload your process log file
                2. Select mining algorithm
                3. Configure parameters
                4. Visualize your process
                """)
            
            st.divider()

    def display_file_upload(self, file_types: list[str]):
        """Displays the file upload component.

        Parameters
        ----------
        file_types : list[str]
            The allowed file types.
        """
        with self.content_column:
            st.markdown("### 📤 Upload your process log file")
            uploaded_file = st.file_uploader(
            label=f"Supported formats: {', '.join(file_types)}",
            type=file_types,
            accept_multiple_files=False,
            key="uploaded_file",
            )

    def display_model_import(self, model):
        """Displays the model import component. A dropdown is displayed to select the mining algorithm.

        Parameters
        ----------
        model : MiningInterface
            The mining model to be imported.
        """
        with self.content_column:
            algorithm_col, _, button_column = st.columns([2, 2, 1])
            with algorithm_col:
                selection = st.selectbox(
                    "Mining Algorthm", list(algorithm_mappings.keys())
                )

            with button_column:
                st.write("")
                navigation_button(
                    label="Import Model",
                    route="Algorithm",
                    use_container_width=True,
                    beforeNavigate=self.controller.set_model_and_algorithm,
                    args=(model, algorithm_mappings[selection]),
                )

    def display_df_import(self, detected_delimiter):
        """Displays the dataframe import component. A text input is displayed to enter the delimiter.

        Parameters
        ----------
        detected_delimiter : str
            The detected delimiter of the CSV file.
        """
        with self.content_column:
            st.markdown("""
            <style>
                div.stButton {
                display: flex;
                justify-content: center; /* Centers horizontally */
                align-items: center; /* Aligns content vertically (if needed) */
             }   
             div.stButton > button {
             width: 50rem; /* Adjust button width */
            }
             </style>
                """, unsafe_allow_html=True)

            st.markdown("### 🔧 Import Settings")

            delimiter = st.text_input(
                "Delimiter",
                value=detected_delimiter,
                help=f"Detected delimiter: '{detected_delimiter}'. Adjust if necessary.",
                label_visibility="visible"
            )



            navigation_button(
                label="Proceed ➡️",
                route="ColumnSelection",
                use_container_width=True,
                beforeNavigate=self.controller.set_df,
                args=(delimiter,),
            )
