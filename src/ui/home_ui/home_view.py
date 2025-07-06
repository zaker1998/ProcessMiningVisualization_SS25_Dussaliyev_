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
        # Note: Base CSS is now handled by the BaseView._apply_theme_css method
        
        with self.content_column:
            st.title("🚀 Process Mining Visualization")
            
            # Welcome message with brief explanation and micro-interactions
            st.markdown("""
            <div class="highlight-card">
                <p style="font-size: 18px; font-weight: 500;">Welcome to your process mining visualization tool!</p>
                <p style="font-size: 16px;">This application helps you analyze and visualize business processes from event logs, making it easier to understand process flows and identify optimization opportunities.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Feature highlights in a grid with improved styling and consistent sizing
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="highlight-card">
                    <div class="section-header">📊 Key Features</div>
                    <div class="feature-item">
                        <span class="feature-icon">📈</span> Intuitive process log visualization
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🔍</span> Multiple mining algorithms
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🔄</span> Interactive dependency graphs
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">💾</span> Easy data import/export
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🔧</span> File format converter
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown("""
                <div class="highlight-card">
                    <div class="section-header">🎯 Getting Started</div>
                    <div class="feature-item">
                             <span class="feature-icon">1.</span> Upload your process log file below
                    </div>
                    <div class="feature-item">
                            <span class="feature-icon">2.</span> Select your preferred mining algorithm
                    </div>
                    <div class="feature-item">
                            <span class="feature-icon">3.</span> Configure parameters as needed
                    </div>
                    <div class="feature-item">
                            <span class="feature-icon">4.</span> Explore your visualized process
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()

    def display_file_upload(self, file_types: list[str]):
        """Displays the file upload component.

        Parameters
        ----------
        file_types : list[str]
            The allowed file types.
        """
        with self.content_column:
            st.markdown("""
            <div class="highlight-card">
                <h3>📤 Upload your process log file</h3>
                <p>Select a file from your computer to begin analyzing your process data.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Add a helpful tooltip/explanation about file formats
            file_format_help = """
            - CSV: Comma-separated values files with event logs
            - XES: eXtensible Event Stream files (IEEE standard for process mining)
            - Pickle/PKL: Serialized Python objects with process models
            """
            
            uploaded_file = st.file_uploader(
                label=f"Supported formats: {', '.join(file_types)}",
                type=file_types,
                accept_multiple_files=False,
                key="uploaded_file",
                help=file_format_help
            )
            
            # Remove the redundant "Load Sample" button since we now have the sample data section in the controller

    def display_model_import(self, model):
        """Displays the model import component. A dropdown is displayed to select the mining algorithm.

        Parameters
        ----------
        model : MiningInterface
            The mining model to be imported.
        """
        with self.content_column:
            st.markdown("""
            <div class="highlight-card">
                <h3>🧮 Select Mining Algorithm</h3>
                <p>Choose the algorithm that best suits your process mining needs.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Add algorithm descriptions to help users make informed choices
            algorithm_descriptions = {
                "Alpha Miner": "Best for well-structured processes with clear patterns",
                "Heuristic Miner": "Handles noise and exceptions in process logs",
                "Inductive Miner": "Creates process trees and handles incomplete logs",
                "Fuzzy Miner": "Ideal for unstructured processes with many variations"
            }
            
            # Create columns with better proportions
            algorithm_col, button_column = st.columns([3, 1])
            
            with algorithm_col:
                selection = st.selectbox(
                    "Mining Algorithm",
                    list(algorithm_mappings.keys()),
                    help="Each algorithm has different strengths. Hover over options to learn more."
                )
                
                # Display description of selected algorithm
                if selection in algorithm_descriptions:
                    st.markdown(f"<p style='font-size: 0.9em; color: #555;'>{algorithm_descriptions[selection]}</p>", 
                                unsafe_allow_html=True)

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
            <div class="highlight-card">
                <h3>🔧 Import Settings</h3>
                <p>Configure how your data should be imported for analysis.</p>
            </div>
            """, unsafe_allow_html=True)

            # Create a more intuitive delimiter selection
            st.markdown("#### File Delimiter")
            
            # Common delimiters with visual representation
            common_delimiters = {
                ",": "Comma (,)",
                ";": "Semicolon (;)",
                "\\t": "Tab (\\t)",
                "|": "Pipe (|)",
                " ": "Space ( )"
            }
            
            # If detected delimiter is in common list, use it as default
            default_index = list(common_delimiters.keys()).index(detected_delimiter) if detected_delimiter in common_delimiters else 0
            
            # Use radio buttons for common delimiters and text input for custom
            delimiter_type = st.radio(
                "Select delimiter type:",
                ["Common delimiter", "Custom delimiter"],
                horizontal=True
            )
            
            if delimiter_type == "Common delimiter":
                delimiter = st.selectbox(
                    "Choose delimiter:",
                    options=list(common_delimiters.values()),
                    index=default_index
                )
                # Extract the actual delimiter character from the selection
                delimiter = list(common_delimiters.keys())[list(common_delimiters.values()).index(delimiter)]
            else:
                delimiter = st.text_input(
                    "Enter custom delimiter:",
                    value=detected_delimiter,
                    help=f"Detected delimiter: '{detected_delimiter}'. Enter your custom delimiter here."
                )
            
            # Preview section
            st.markdown("#### Data Preview")
            st.info("A preview of your data will appear here after setting the delimiter.")
            
            # Proceed button with more descriptive text
            st.markdown("#### Continue to Column Selection")
            navigation_button(
                label="Proceed to Column Selection ➡️",
                route="ColumnSelection",
                use_container_width=True,
                beforeNavigate=self.controller.set_df,
                args=(delimiter,),
            )

    def display_file_converter(self):
        """Displays the file converter component for converting between different formats."""
        with self.content_column:
            st.markdown("""
            <div class="highlight-card">
                <h3>🔄 File Format Converter</h3>
                <p>Convert your process log files between different formats (CSV ↔ XES)</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create tabs for different conversion options
            tab1, tab2 = st.tabs(["📊 CSV to XES", "📄 XES to CSV"])
            
            with tab1:
                st.markdown("#### Convert CSV to XES Format")
                st.markdown("Upload a CSV file and convert it to XES format for use with process mining tools.")
                
                csv_file = st.file_uploader(
                    "Choose CSV file",
                    type=['csv'],
                    key="csv_to_xes_uploader",
                    help="Upload a CSV file containing event log data"
                )
                
                if csv_file is not None:
                    # Delimiter selection for CSV
                    st.markdown("**Delimiter Settings:**")
                    delimiter_col1, delimiter_col2 = st.columns(2)
                    
                    with delimiter_col1:
                        delimiter_type = st.radio(
                            "Delimiter type:",
                            ["Auto-detect", "Custom"],
                            key="csv_delimiter_type",
                            horizontal=True
                        )
                    
                    with delimiter_col2:
                        if delimiter_type == "Custom":
                            delimiter = st.text_input(
                                "Enter delimiter:",
                                value=",",
                                key="csv_custom_delimiter"
                            )
                        else:
                            delimiter = "auto"
                    
                    # Column mapping section
                    st.markdown("**Column Mapping:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        case_id_col = st.text_input(
                            "Case ID Column:",
                            value="case_id",
                            key="csv_case_id_col",
                            help="Column name for case/trace identifiers"
                        )
                    
                    with col2:
                        activity_col = st.text_input(
                            "Activity Column:",
                            value="activity",
                            key="csv_activity_col",
                            help="Column name for activity names"
                        )
                    
                    with col3:
                        timestamp_col = st.text_input(
                            "Timestamp Column:",
                            value="timestamp",
                            key="csv_timestamp_col",
                            help="Column name for timestamps"
                        )
                    
                    # Convert button
                    if st.button("🔄 Convert to XES", key="convert_csv_to_xes", use_container_width=True):
                        self.controller.convert_csv_to_xes(
                            csv_file, delimiter, case_id_col, activity_col, timestamp_col
                        )
            
            with tab2:
                st.markdown("#### Convert XES to CSV Format")
                st.markdown("Upload an XES file and convert it to CSV format for easier data manipulation.")
                
                xes_file = st.file_uploader(
                    "Choose XES file",
                    type=['xes'],
                    key="xes_to_csv_uploader",
                    help="Upload an XES file to convert to CSV format"
                )
                
                if xes_file is not None:
                    # Options for CSV output
                    st.markdown("**CSV Output Options:**")
                    csv_col1, csv_col2 = st.columns(2)
                    
                    with csv_col1:
                        csv_delimiter = st.selectbox(
                            "CSV Delimiter:",
                            [",", ";", "\t", "|"],
                            key="xes_csv_delimiter",
                            format_func=lambda x: {"," : "Comma (,)", ";" : "Semicolon (;)", "\t" : "Tab", "|" : "Pipe (|)"}[x]
                        )
                    
                    with csv_col2:
                        include_all_attributes = st.checkbox(
                            "Include all attributes",
                            value=False,
                            key="include_all_attrs",
                            help="Include all event and case attributes in the CSV output"
                        )
                    
                    # Convert button
                    if st.button("🔄 Convert to CSV", key="convert_xes_to_csv", use_container_width=True):
                        self.controller.convert_xes_to_csv(
                            xes_file, csv_delimiter, include_all_attributes
                        )
            
            st.divider()
