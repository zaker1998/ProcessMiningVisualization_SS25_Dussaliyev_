import streamlit as st
import os
import time
from ui.base_ui.base_controller import BaseController
from analysis.detection_model import DetectionModel
from io_operations.import_operations import ImportOperations
from exceptions.io_exceptions import (
    UnsupportedFileTypeException,
    NotImplementedFileTypeException,
)
from logger import get_logger
from utils import validate_event_log, timed_execution


class HomeController(BaseController):
    """Controller for the Home page."""

    def __init__(
        self,
        views=None,
        detection_model: DetectionModel = None,
        import_model: ImportOperations = None,
        supported_file_types: list[str] = None,
    ):
        """Initializes the controller for the Home page.

        Parameters
        ----------
        views :  List[BaseView] | BaseView, optional
            The views for the Home page. If None is passed, the HomeView is used, by default None
        detection_model : DetectionModel, optional
            The detection model for detecting file types and delimiters. If None is passed, a new instance is created, by default None
        import_model : ImportOperations, optional
            The import operations model for reading files. If None is passed, a new instance is created, by default None
        supported_file_types : list[str], optional
            The supported file types. If None is passed, the file suffixes from the config file are used, by default None
        """
        self.detection_model = DetectionModel() if detection_model is None else detection_model
        self.import_model = ImportOperations() if import_model is None else import_model
        if views is None:
            from ui.home_ui.home_view import HomeView

            views = [HomeView()]
        super().__init__(views)
        self.logger = get_logger("HomeController")

        if supported_file_types is None:
            from config import import_file_suffixes

            supported_file_types = import_file_suffixes

        self.supported_file_types = supported_file_types
        
        # Initialize sample data paths
        self.sample_files = self._get_sample_files()

    def _get_sample_files(self):
        """Get available sample files to showcase the application."""
        samples = []
        sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sample_data")
        
        if os.path.exists(sample_dir):
            # Get CSV files from sample_data directory
            for file in os.listdir(sample_dir):
                if file.endswith(".csv"):
                    samples.append({
                        "name": file.replace(".csv", "").replace("_", " ").title(),
                        "path": os.path.join(sample_dir, file),
                        "type": "csv"
                    })
            
            # Get XES files from sample_data/xes_examples directory
            xes_dir = os.path.join(sample_dir, "xes_examples")
            if os.path.exists(xes_dir):
                for file in os.listdir(xes_dir):
                    if file.endswith(".xes"):
                        samples.append({
                            "name": file.replace(".xes", "").replace("_", " ").title() + " (XES)",
                            "path": os.path.join(xes_dir, file),
                            "type": "xes"
                        })
        
        return samples

    def get_page_title(self) -> str:
        """Returns the page title."""
        return ""

    def process_session_state(self):
        """Processes the session state. Checks if a file has been uploaded and stores it in a instance variable."""
        super().process_session_state()
        self.uploaded_file = st.session_state.get("uploaded_file", None)

    @timed_execution
    def process_file(self, selected_view):
        """Processes the uploaded file and displays the import view.
        The file type is detected and the view is displayed accordingly.

        Parameters
        ----------
        selected_view : BaseView
            The view to display the import view.
        """
        if self.uploaded_file is None:
            return

        try:
            with st.spinner("Processing uploaded file..."):
                file_type = self.detection_model.detect_file_type(self.uploaded_file)

                if file_type == "csv":
                    line = self.import_model.read_line(self.uploaded_file)
                    detected_delimiter = self.detection_model.detect_delimiter(line)
                    self.uploaded_file.seek(0)
                    selected_view.display_df_import(detected_delimiter)
                elif file_type == "pickle":
                    model = self.import_model.read_model(self.uploaded_file)
                    selected_view.display_model_import(model)
                elif file_type == "xes":
                    # Process XES file
                    with st.spinner("Importing XES file..."):
                        # Validate XES file
                        if not self.import_model.validate_xes(self.uploaded_file):
                            raise UnsupportedFileTypeException("Invalid XES file format")
                        
                        # Import XES and convert to DataFrame
                        event_log = self.import_model.read_xes(self.uploaded_file)
                        df = self.import_model.xes_to_dataframe(event_log)
                        
                        # Rename columns to more user-friendly names for consistency
                        df = df.rename(columns={
                            'case:concept:name': 'case_id',
                            'concept:name': 'activity',
                            'time:timestamp': 'timestamp'
                        })
                        
                        # Store dataframe in session state
                        st.session_state.df = df
                        
                        # Navigate directly to the ColumnSelection page
                        st.session_state.page = "ColumnSelection"
                        st.rerun()
                else:
                    raise NotImplementedFileTypeException(file_type)
        except UnsupportedFileTypeException as e:
            self.logger.exception(e)
            st.session_state.error = e.message
            st.rerun()
        except NotImplementedFileTypeException as e:
            self.logger.exception(e)
            st.session_state.error = e.message
            st.rerun()
        except Exception as e:
            self.logger.exception(e)
            st.session_state.error = f"Error processing file: {str(e)}"
            st.rerun()

    def set_model_and_algorithm(self, model, algorithm: str):
        """Sets the model and algorithm in the session state before navigating to the Algorithm page.

        Parameters
        ----------
        model : MiningInterface
            The mining model to be imported.
        algorithm : str
            The chosen algorithm.
        """
        st.session_state.model = model
        st.session_state.algorithm = algorithm

    @timed_execution
    def set_df(self, delimiter: str):
        """creates a dataframe from the uploaded file with the given delimiter.
        Stores the dataframe in the session state and changes the routing to the ColumnSelection page.

        Parameters
        ----------
        delimiter : str
            The delimiter to be used for the CSV file.
        """
        if delimiter == "":
            st.session_state.error = "Please enter a delimiter"
            # change routing to home
            st.session_state.page = "Home"
            return
            
        with st.spinner("Reading and processing data..."):
            df = self.import_model.read_csv(self.uploaded_file, delimiter)
            
            # Validate the event log
            is_valid, message = validate_event_log(df)
            if not is_valid:
                st.session_state.error = f"Invalid event log: {message}"
                # change routing to home
                st.session_state.page = "Home"
                return
                
            # Store dataframe in session state
            st.session_state.df = df

    def run(self, selected_view, index):
        """Runs the controller for the Home page. This method is called to display the Home page and to react to user input.

        Parameters
        ----------
        selected_view : BaseView
            The view to display the import view.
        index : int
            The index of the selected view.
        """
        self.selected_view = selected_view
        selected_view.display_intro()
        
        # Display file converter section
        selected_view.display_file_converter()
        
        # Display file upload
        selected_view.display_file_upload(self.supported_file_types)
        
        # Add sample data section - simplified and better aligned
        if self.sample_files:
            # Use markdown with HTML for better styling
            st.markdown("""
            <div class="sample-data-section">
                <p>New to process mining? Try using our sample files to get started.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Use columns to display sample buttons in a cleaner way
            cols = st.columns([1, 1, 1])
            
            with cols[0]:
                st.markdown('<p class="sample-data-header">📊 Sample Datasets</p>', unsafe_allow_html=True)
            
            for idx, sample in enumerate(self.sample_files):
                with cols[idx % 2 + 1]:
                    # Add custom key to avoid conflicts
                    button_key = f"sample_{sample['name']}_{idx}"
                    if st.button(f"{sample['name']}", key=button_key, use_container_width=True):
                        self.load_sample_file(sample['path'])
        
        # Process uploaded file if any
        if self.uploaded_file is not None:
            self.process_file(selected_view)

    @timed_execution
    def load_sample_file(self, file_path: str):
        """Loads a sample file from the given path and proceeds directly to the next page.
        
        Parameters
        ----------
        file_path : str
            The path to the sample file
        """
        try:
            with st.spinner("Loading sample data..."):
                # Detect the file type based on extension
                file_type = "csv" if file_path.endswith(".csv") else "xes" if file_path.endswith(".xes") else None
                
                if file_type == "csv":
                    # Load the CSV file with comma delimiter (most common)
                    df = self.import_model.read_csv(file_path, delimiter=",")
                elif file_type == "xes":
                    # Load the XES file
                    event_log = self.import_model.read_xes(file_path)
                    df = self.import_model.xes_to_dataframe(event_log)
                    
                    # Rename columns to more user-friendly names for consistency
                    df = df.rename(columns={
                        'case:concept:name': 'case_id',
                        'concept:name': 'activity',
                        'time:timestamp': 'timestamp'
                    })
                else:
                    raise UnsupportedFileTypeException(f"Unknown file type for {file_path}")
                
                # Validate the event log
                is_valid, message = validate_event_log(df)
                if not is_valid:
                    st.session_state.error = f"Invalid sample data: {message}"
                    return
                    
                # Store the dataframe in session state
                st.session_state.df = df
                
                # Navigate directly to the ColumnSelection page
                st.session_state.page = "ColumnSelection"
                st.rerun()
        except Exception as e:
            self.logger.exception(e)
            st.session_state.error = f"Error loading sample file: {str(e)}"
            st.rerun()

    @timed_execution
    def convert_csv_to_xes(self, csv_file, delimiter, case_id_col, activity_col, timestamp_col):
        """Converts a CSV file to XES format and provides download.
        
        Parameters
        ----------
        csv_file : UploadedFile
            The uploaded CSV file
        delimiter : str
            The delimiter to use for CSV parsing
        case_id_col : str
            The column name for case IDs
        activity_col : str
            The column name for activities
        timestamp_col : str
            The column name for timestamps
        """
        try:
            with st.spinner("Converting CSV to XES..."):
                # Auto-detect delimiter if needed
                if delimiter == "auto":
                    line = self.import_model.read_line(csv_file)
                    delimiter = self.detection_model.detect_delimiter(line)
                    csv_file.seek(0)
                
                # Read the CSV file
                df = self.import_model.read_csv(csv_file, delimiter)
                
                # Validate required columns exist
                required_cols = [case_id_col, activity_col, timestamp_col]
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"Missing columns in CSV: {', '.join(missing_cols)}")
                    st.info(f"Available columns: {', '.join(df.columns.tolist())}")
                    return
                
                # Show data preview before conversion
                st.subheader("📋 Data Preview (First 5 rows)")
                preview_df = df[[case_id_col, activity_col, timestamp_col]].head()
                st.dataframe(preview_df, use_container_width=True)
                
                # Rename columns to standard XES format
                df = df.rename(columns={
                    case_id_col: 'case:concept:name',
                    activity_col: 'concept:name',
                    timestamp_col: 'time:timestamp'
                })
                
                # Ensure proper data types for XES format
                import pandas as pd
                
                # Convert case ID to string (required for XES)
                df['case:concept:name'] = df['case:concept:name'].astype(str)
                
                # Convert activity to string (required for XES)
                df['concept:name'] = df['concept:name'].astype(str)
                
                # Convert timestamp column to datetime if it's not already
                if not pd.api.types.is_datetime64_any_dtype(df['time:timestamp']):
                    try:
                        df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])
                    except Exception as e:
                        st.error(f"Error converting timestamp column: {str(e)}")
                        return
                
                # Remove any rows with null values in critical columns
                df = df.dropna(subset=['case:concept:name', 'concept:name', 'time:timestamp'])
                
                if len(df) == 0:
                    st.error("No valid data remaining after processing. Please check your data for missing values.")
                    return
                
                # Export to XES bytes
                from io_operations.export_operations import ExportOperations
                export_ops = ExportOperations()
                xes_bytes = export_ops.export_to_xes_bytes(df)
                
                # Generate filename
                original_filename = csv_file.name.replace('.csv', '')
                xes_filename = f"{original_filename}_converted.xes"
                
                # Display success message with data summary
                st.success("✅ CSV successfully converted to XES format!")
                
                # Show conversion summary
                st.info(f"📊 Conversion Summary:\n"
                        f"- Cases: {df['case:concept:name'].nunique()}\n"
                        f"- Activities: {df['concept:name'].nunique()}\n"
                        f"- Events: {len(df)}\n"
                        f"- Date range: {df['time:timestamp'].min()} to {df['time:timestamp'].max()}")
                
                st.download_button(
                    label="📥 Download XES File",
                    data=xes_bytes,
                    file_name=xes_filename,
                    mime="application/xml",
                    key="download_xes_file"
                )
                
        except Exception as e:
            self.logger.exception(e)
            st.error(f"Error converting CSV to XES: {str(e)}")

    @timed_execution
    def convert_xes_to_csv(self, xes_file, csv_delimiter, include_all_attributes):
        """Converts an XES file to CSV format and provides download.
        
        Parameters
        ----------
        xes_file : UploadedFile
            The uploaded XES file
        csv_delimiter : str
            The delimiter to use for CSV output
        include_all_attributes : bool
            Whether to include all attributes in the CSV
        """
        try:
            with st.spinner("Converting XES to CSV..."):
                # Read the XES file
                event_log = self.import_model.read_xes(xes_file)
                
                # Convert to DataFrame
                df = self.import_model.xes_to_dataframe(event_log)
                
                # If not including all attributes, keep only the essential columns
                if not include_all_attributes:
                    # Standard columns to keep
                    standard_cols = ['case:concept:name', 'concept:name', 'time:timestamp']
                    
                    # Find which standard columns exist in the DataFrame
                    existing_standard_cols = [col for col in standard_cols if col in df.columns]
                    
                    if existing_standard_cols:
                        df = df[existing_standard_cols]
                    
                    # Rename to more user-friendly names
                    df = df.rename(columns={
                        'case:concept:name': 'case_id',
                        'concept:name': 'activity',
                        'time:timestamp': 'timestamp'
                    })
                
                # Convert DataFrame to CSV
                csv_buffer = df.to_csv(sep=csv_delimiter, index=False)
                
                # Generate filename
                original_filename = xes_file.name.replace('.xes', '')
                csv_filename = f"{original_filename}_converted.csv"
                
                # Display success message and download button
                st.success("✅ XES successfully converted to CSV format!")
                
                # Show preview of the data
                st.subheader("📋 Data Preview:")
                st.dataframe(df.head(10), use_container_width=True)
                
                st.download_button(
                    label="📥 Download CSV File",
                    data=csv_buffer,
                    file_name=csv_filename,
                    mime="text/csv",
                    key="download_csv_file"
                )
                
        except Exception as e:
            self.logger.exception(e)
            st.error(f"Error converting XES to CSV: {str(e)}")
