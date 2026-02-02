from core.graphs.visualization.base_graph import BaseGraph
import pickle
from exceptions.io_exceptions import (
    UnsupportedFileTypeException,
    NotImplementedFileTypeException,
)
from exceptions.type_exceptions import InvalidTypeException
import pandas as pd
import os
import tempfile
import logging
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET
from datetime import datetime


class ExportOperations:

    def __init__(self, supported_graph_export_formats=None):
        """Initializes the ExportOperations class.

        Parameters
        ----------
        supported_graph_export_formats : List[str], optional
            The supported graph export formats, by default None
        """
        if supported_graph_export_formats is None:
            from config import graph_export_formats

            supported_graph_export_formats = graph_export_formats

        self.graph_export_formats = supported_graph_export_formats

    def export_graph(
        self, graph: BaseGraph, filename: str, format: str = "png", dpi=96
    ) -> str:
        """Export a graph to a file.

        Parameters
        ----------
        graph : BaseGraph
            The graph to export
        filename : str
            The name of the file to export the graph to
        format : str, optional
            The format of the exported file, by default "png"
        dpi : int, optional
            The DPI of the exported file. Only considered if the format is png, by default 96

        Returns
        -------
        str
            The actual filename that was used (may be different if temporary directory was used)

        Raises
        ------
        InvalidTypeException
            If graph is not an instance of BaseGraph
        UnsupportedFileTypeException
            If the export format is not supported
        NotImplementedFileTypeException
            If the export format is not implemented
        """

        if not isinstance(graph, BaseGraph):
            raise InvalidTypeException(BaseGraph, type(graph))

        if format not in self.graph_export_formats:
            raise UnsupportedFileTypeException(format)

        # Use a robust approach that prefers temporary files to avoid permission issues
        use_filename = None
        
        # On Windows or when dealing with temp directories, use system temp by default
        import platform
        if platform.system() == "Windows" or "temp" in filename.lower():
            logging.info("Using temporary directory for better Windows compatibility")
            base_filename = os.path.basename(filename) or "graph"
            # Create a temporary file that we know we can write to
            temp_fd, temp_path = tempfile.mkstemp(prefix=base_filename + "_", suffix="", dir=tempfile.gettempdir())
            os.close(temp_fd)  # Close the file descriptor, but keep the path
            os.remove(temp_path)  # Remove the temp file, we just need the safe path
            use_filename = temp_path
            logging.info(f"Using temporary file: {use_filename}")
        else:
            # For non-Windows systems, try the original approach with fallback
            try:
                # First try to use the requested filename
                dirname = os.path.dirname(filename)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)
                
                # Test if we can actually write to this location
                test_file = filename + "_test"
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    # If we get here, the directory is writable
                    use_filename = filename
                except (OSError, PermissionError):
                    raise OSError("Cannot write to requested location")
                    
            except OSError:
                # If we can't use the requested location, use a proper temporary file
                logging.warning(f"Could not write to requested location {filename}. Using temporary directory.")
                base_filename = os.path.basename(filename) or "graph"
                
                # Create a temporary file that we know we can write to
                temp_fd, temp_path = tempfile.mkstemp(prefix=base_filename + "_", suffix="", dir=tempfile.gettempdir())
                os.close(temp_fd)  # Close the file descriptor, but keep the path
                os.remove(temp_path)  # Remove the temp file, we just need the safe path
                use_filename = temp_path
                logging.info(f"Using temporary file: {use_filename}")

        graphviz_graph = graph.get_graphviz_graph()
        export_format = format.lower()

        if export_format == "png":
            graphviz_graph.attr(dpi=str(dpi))
            graphviz_graph.render(use_filename, format=export_format, cleanup=True)
            graphviz_graph.attr(dpi="0")
        elif export_format in ["svg", "dot"]:
            graphviz_graph.render(use_filename, format=export_format, cleanup=True)
        else:
            raise NotImplementedFileTypeException(export_format)
        
        # Return the actual filename with the correct extension
        return use_filename + "." + export_format

    def export_model_to_file(self, model, filename: str) -> None:
        """Export a model to a file.

        Parameters
        ----------
        model : object
            The model to export
        filename : str
            The name of the file to export the model to
        """
        if not filename.endswith(".pickle"):
            filename += ".pickle"

        with open(filename, "wb") as file:
            pickle.dump(model, file)

    def export_model_to_bytes(self, model) -> bytes:
        """Export a model to bytes.

        Parameters
        ----------
        model : object
            The model to export

        Returns
        -------
        bytes
            The model as bytes
        """
        return pickle.dumps(model)

    def export_to_xes(self, data: pd.DataFrame, filename: str) -> None:
        """Export data to an XES file.

        Parameters
        ----------
        data : pd.DataFrame
            The data to export as a pandas DataFrame
        filename : str
            The name of the file to export the data to

        Raises
        ------
        InvalidTypeException
            If data is not a pandas DataFrame
        """
        if not isinstance(data, pd.DataFrame):
            raise InvalidTypeException("pandas DataFrame", type(data))
            
        if not filename.endswith(".xes"):
            filename += ".xes"
            
        # Create directory if it doesn't exist
        dirname = os.path.dirname(filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        try:
            self._write_xes_native(data, filename)
        except Exception as e:
            logging.error(f"Error exporting to XES: {str(e)}")
            raise Exception(f"Failed to export to XES: {str(e)}")
    
    def _write_xes_native(
        self,
        df: pd.DataFrame,
        filename: str,
        case_id_col: str = "case:concept:name",
        activity_col: str = "concept:name",
        timestamp_col: str = "time:timestamp",
        log_attributes: Optional[Dict[str, Any]] = None,
        trace_attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write a DataFrame to XES format using native XML processing.
        
        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to export
        filename : str
            The output file path
        case_id_col : str
            Column name for case IDs
        activity_col : str
            Column name for activity names
        timestamp_col : str
            Column name for timestamps
        log_attributes : Dict[str, Any], optional
            Log-level attributes
        trace_attributes : Dict[str, Any], optional
            Trace-level attributes
        """
        # Create the root element with XES namespace
        root = ET.Element("log")
        root.set("xes.version", "1.0")
        root.set("xes.features", "nested-attributes")
        root.set("xmlns", "http://www.xes-standard.org/")
        
        # Add log-level attributes
        if log_attributes:
            for key, value in log_attributes.items():
                self._add_attribute(root, key, value)
        
        # Detect column names - support common variations
        actual_case_col = self._find_column(df, [case_id_col, "case:concept:name", "Case ID", "case_id", "CaseID"])
        actual_activity_col = self._find_column(df, [activity_col, "concept:name", "Activity", "activity", "event"])
        actual_timestamp_col = self._find_column(df, [timestamp_col, "time:timestamp", "Timestamp", "timestamp", "time"])
        
        if actual_case_col is None:
            raise ValueError(f"Could not find case ID column. Tried: {case_id_col}")
        if actual_activity_col is None:
            raise ValueError(f"Could not find activity column. Tried: {activity_col}")
        
        # Get list of additional attribute columns
        standard_cols = {actual_case_col, actual_activity_col, actual_timestamp_col}
        additional_cols = [col for col in df.columns if col not in standard_cols and col is not None]
        
        # Group by case ID
        grouped = df.groupby(actual_case_col)
        
        for case_id, group in grouped:
            trace_elem = ET.SubElement(root, "trace")
            
            # Add trace name
            name_elem = ET.SubElement(trace_elem, "string")
            name_elem.set("key", "concept:name")
            name_elem.set("value", str(case_id))
            
            # Add trace-level attributes
            if trace_attributes:
                for key, value in trace_attributes.items():
                    self._add_attribute(trace_elem, key, value)
            
            # Sort by timestamp if available
            if actual_timestamp_col and actual_timestamp_col in group.columns:
                group = group.sort_values(by=actual_timestamp_col)
            
            # Add events
            for _, row in group.iterrows():
                event_elem = ET.SubElement(trace_elem, "event")
                
                # Add activity name
                activity_elem = ET.SubElement(event_elem, "string")
                activity_elem.set("key", "concept:name")
                activity_elem.set("value", str(row[actual_activity_col]))
                
                # Add timestamp if available
                ts_value = row.get(actual_timestamp_col) if actual_timestamp_col else None
                if actual_timestamp_col and ts_value is not None and not pd.isna(ts_value):
                    ts_elem = ET.SubElement(event_elem, "date")
                    ts_elem.set("key", "time:timestamp")
                    if isinstance(ts_value, datetime):
                        ts_elem.set("value", ts_value.isoformat())
                    elif isinstance(ts_value, pd.Timestamp):
                        ts_elem.set("value", ts_value.isoformat())
                    else:
                        ts_elem.set("value", str(ts_value))
                
                # Add additional attributes
                for col in additional_cols:
                    col_value = row.get(col)
                    if col_value is not None and not pd.isna(col_value):
                        self._add_attribute(event_elem, col, col_value)
        
        # Write to file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(filename, encoding="utf-8", xml_declaration=True)
    
    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        """Find the first matching column from a list of candidates.
        
        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to search
        candidates : List[str]
            List of potential column names
            
        Returns
        -------
        Optional[str]
            The first matching column name, or None if not found
        """
        for col in candidates:
            if col in df.columns:
                return col
        return None
    
    def _add_attribute(self, parent: ET.Element, key: str, value: Any) -> None:
        """Add an attribute element to a parent element.
        
        Parameters
        ----------
        parent : ET.Element
            The parent element
        key : str
            The attribute key
        value : Any
            The attribute value
        """
        import numpy as np
        
        # Handle numpy bool before regular bool (numpy.bool_ is also instance of bool in some cases)
        if isinstance(value, (np.bool_, bool)):
            elem = ET.SubElement(parent, "boolean")
            elem.set("key", key)
            elem.set("value", str(bool(value)).lower())
        elif isinstance(value, (np.integer, int)):
            elem = ET.SubElement(parent, "int")
            elem.set("key", key)
            elem.set("value", str(int(value)))
        elif isinstance(value, (np.floating, float)):
            # Check for NaN/inf
            if np.isnan(value) or np.isinf(value):
                return  # Skip NaN/inf values
            elem = ET.SubElement(parent, "float")
            elem.set("key", key)
            elem.set("value", str(float(value)))
        elif isinstance(value, (datetime, pd.Timestamp, np.datetime64)):
            elem = ET.SubElement(parent, "date")
            elem.set("key", key)
            if isinstance(value, np.datetime64):
                value = pd.Timestamp(value)
            elem.set("value", value.isoformat() if hasattr(value, 'isoformat') else str(value))
        else:
            elem = ET.SubElement(parent, "string")
            elem.set("key", key)
            elem.set("value", str(value))
            
    def export_dataframe_to_xes(
        self, 
        df: pd.DataFrame, 
        filename: str,
        case_id_col: str = "case:concept:name",
        activity_col: str = "concept:name",
        timestamp_col: str = "time:timestamp",
        additional_attributes: Optional[List[str]] = None
    ) -> None:
        """Export a pandas DataFrame to an XES file with specified column mappings.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to export
        filename : str
            The name of the file to export the data to
        case_id_col : str, optional
            The column containing case IDs, by default "case:concept:name"
        activity_col : str, optional
            The column containing activity names, by default "concept:name"
        timestamp_col : str, optional
            The column containing timestamps, by default "time:timestamp"
        additional_attributes : List[str], optional
            Additional columns to include in the XES file, by default None

        Raises
        ------
        InvalidTypeException
            If data is not a pandas DataFrame
        """
        if not isinstance(df, pd.DataFrame):
            raise InvalidTypeException("pandas DataFrame", type(df))
            
        if not filename.endswith(".xes"):
            filename += ".xes"
            
        # Create directory if it doesn't exist
        dirname = os.path.dirname(filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
            
        try:
            self._write_xes_native(
                df, 
                filename, 
                case_id_col=case_id_col, 
                activity_col=activity_col, 
                timestamp_col=timestamp_col
            )
        except Exception as e:
            logging.error(f"Error exporting DataFrame to XES: {str(e)}")
            raise Exception(f"Failed to export DataFrame to XES: {str(e)}")
            
    def export_logs_with_attributes(
        self,
        data: pd.DataFrame,
        filename: str,
        log_attributes: Optional[Dict[str, Any]] = None,
        trace_attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Export data to an XES file with custom log and trace attributes.

        Parameters
        ----------
        data : pd.DataFrame
            The data to export as a pandas DataFrame
        filename : str
            The name of the file to export the data to
        log_attributes : Dict[str, Any], optional
            Custom log-level attributes to add, by default None
        trace_attributes : Dict[str, Any], optional
            Custom trace-level attributes to add, by default None

        Raises
        ------
        InvalidTypeException
            If data is not a pandas DataFrame
        """
        if not isinstance(data, pd.DataFrame):
            raise InvalidTypeException("pandas DataFrame", type(data))
            
        if not filename.endswith(".xes"):
            filename += ".xes"
            
        # Create directory if it doesn't exist
        dirname = os.path.dirname(filename)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
            
        try:
            self._write_xes_native(
                data, 
                filename, 
                log_attributes=log_attributes,
                trace_attributes=trace_attributes
            )
        except Exception as e:
            logging.error(f"Error exporting logs with attributes: {str(e)}")
            raise Exception(f"Failed to export logs with attributes: {str(e)}")
            
    def export_to_xes_bytes(self, data: pd.DataFrame) -> bytes:
        """Export data to XES format and return as bytes.

        Parameters
        ----------
        data : pd.DataFrame
            The data to export as a pandas DataFrame

        Returns
        -------
        bytes
            The XES file as bytes

        Raises
        ------
        InvalidTypeException
            If data is not a pandas DataFrame
        """
        if not isinstance(data, pd.DataFrame):
            raise InvalidTypeException("pandas DataFrame", type(data))
            
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xes') as temp_file:
                temp_path = temp_file.name
                
            # Write to temporary file using native method
            self._write_xes_native(data, temp_path)
                
            # Read the file as bytes
            with open(temp_path, 'rb') as file:
                xes_bytes = file.read()
                
            # Clean up the temporary file
            os.unlink(temp_path)
            
            return xes_bytes
        except Exception as e:
            logging.error(f"Error exporting to XES bytes: {str(e)}")
            raise Exception(f"Failed to export to XES bytes: {str(e)}")
