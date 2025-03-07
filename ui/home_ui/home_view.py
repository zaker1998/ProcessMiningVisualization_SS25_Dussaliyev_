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
                    padding-top: 1rem;
                    padding-bottom: 1rem;
                }
            </style>
            """, unsafe_allow_html=True)    
        with self.content_column:
            st.title("🚀 Welcome to the Process Mining Tool")
            st.markdown(
                """
                This tool helps you **visualize dependencies** in your process logs quickly and intuitively.  
                
                **Get started by uploading your log file below** 👇
                """
            )
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
            delimiter_col, _, button_column = st.columns([1, 3, 1])

            with delimiter_col:
                delimiter = st.text_input(
                    "Delimiter", value=detected_delimiter, key="delimiter", max_chars=1
                )

            with button_column:
                st.write("")
                navigation_button(
                    label="Mine from File",
                    route="ColumnSelection",
                    use_container_width=True,
                    beforeNavigate=self.controller.set_df,
                    args=(delimiter,),
                )
