from src.graphs.visualization.base_graph import BaseGraph
import pickle
from src.exceptions.io_exceptions import (
    UnsupportedFileTypeException,
    NotImplementedFileTypeException,
)
from src.exceptions.type_exceptions import InvalidTypeException
import pm4py
import pandas as pd
from pm4py.objects.log.obj import EventLog
import os
import tempfile
import logging
from typing import Dict, Any, List, Union, Optional


class ExportOperations:

    def __init__(self, supported_graph_export_formats=None):
        """Initializes the ExportOperations class.

        Parameters
        ----------
        supported_graph_export_formats : List[str], optional
            The supported graph export formats, by default None
        """
        if supported_graph_export_formats is None:
            from src.config import graph_export_formats

            supported_graph_export_formats = graph_export_formats

        self.graph_export_formats = supported_graph_export_formats

    def export_graph(
        self, graph: BaseGraph, filename: str, format: str = "png", dpi=96
    ) -> None:
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

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        graphviz_graph = graph.get_graphviz_graph()
        export_format = format.lower()

        if export_format == "png":
            graphviz_graph.attr(dpi=str(dpi))
            graphviz_graph.render(filename, format=export_format, cleanup=True)
            graphviz_graph.attr(dpi="0")
        elif export_format in ["svg", "dot"]:
            graphviz_graph.render(filename, format=export_format, cleanup=True)
        else:
            raise NotImplementedFileTypeException(export_format)

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

    def export_to_xes(self, data: Union[pd.DataFrame, EventLog], filename: str) -> None:
        """Export data to an XES file.

        Parameters
        ----------
        data : pd.DataFrame or EventLog
            The data to export, either as a pandas DataFrame or a PM4Py EventLog
        filename : str
            The name of the file to export the data to

        Raises
        ------
        InvalidTypeException
            If data is not a pandas DataFrame or a PM4Py EventLog
        """
        if not filename.endswith(".xes"):
            filename += ".xes"
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        try:
            if isinstance(data, pd.DataFrame):
                # Convert DataFrame to EventLog using PM4Py's converter
                from pm4py.objects.conversion.log import converter as log_converter
                event_log = log_converter.apply(data, variant=log_converter.Variants.TO_EVENT_LOG)
                # Write using XES exporter
                from pm4py.objects.log.exporter.xes import exporter as xes_exporter
                xes_exporter.apply(event_log, filename)
            elif isinstance(data, EventLog):
                # Write EventLog directly using XES exporter
                from pm4py.objects.log.exporter.xes import exporter as xes_exporter
                xes_exporter.apply(data, filename)
            else:
                raise InvalidTypeException("pandas DataFrame or PM4Py EventLog", type(data))
        except Exception as e:
            logging.error(f"Error exporting to XES: {str(e)}")
            raise Exception(f"Failed to export to XES: {str(e)}")
            
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
        os.makedirs(os.path.dirname(filename), exist_ok=True)
            
        try:
            # Create a copy of the DataFrame to avoid modifying the original
            df_copy = df.copy()
            
            # Rename columns to match expected XES format if they don't already match
            columns_mapping = {}
            if case_id_col != "case:concept:name" and case_id_col in df_copy.columns:
                columns_mapping[case_id_col] = "case:concept:name"
                
            if activity_col != "concept:name" and activity_col in df_copy.columns:
                columns_mapping[activity_col] = "concept:name"
                
            if timestamp_col != "time:timestamp" and timestamp_col in df_copy.columns:
                columns_mapping[timestamp_col] = "time:timestamp"
                
            if columns_mapping:
                df_copy = df_copy.rename(columns=columns_mapping)
            
            # Convert to event log and write
            event_log = pm4py.convert_to_event_log(df_copy)
            pm4py.write_xes(event_log, filename)
        except Exception as e:
            logging.error(f"Error exporting DataFrame to XES: {str(e)}")
            raise Exception(f"Failed to export DataFrame to XES: {str(e)}")
            
    def export_logs_with_attributes(
        self,
        data: Union[pd.DataFrame, EventLog],
        filename: str,
        log_attributes: Optional[Dict[str, Any]] = None,
        trace_attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Export data to an XES file with custom log and trace attributes.

        Parameters
        ----------
        data : pd.DataFrame or EventLog
            The data to export, either as a pandas DataFrame or a PM4Py EventLog
        filename : str
            The name of the file to export the data to
        log_attributes : Dict[str, Any], optional
            Custom log-level attributes to add, by default None
        trace_attributes : Dict[str, Any], optional
            Custom trace-level attributes to add, by default None

        Raises
        ------
        InvalidTypeException
            If data is not a pandas DataFrame or a PM4Py EventLog
        """
        if not filename.endswith(".xes"):
            filename += ".xes"
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
            
        try:
            if isinstance(data, pd.DataFrame):
                # Convert DataFrame to EventLog
                event_log = pm4py.convert_to_event_log(data)
            elif isinstance(data, EventLog):
                # Use EventLog directly
                event_log = data
            else:
                raise InvalidTypeException("pandas DataFrame or PM4Py EventLog", type(data))
                
            # Add log-level attributes
            if log_attributes:
                for key, value in log_attributes.items():
                    event_log.attributes[key] = value
                
            # Add trace-level attributes if provided
            if trace_attributes and len(event_log) > 0:
                for trace in event_log:
                    for key, value in trace_attributes.items():
                        trace.attributes[key] = value
                
            # Write to file
            pm4py.write_xes(event_log, filename)
        except Exception as e:
            logging.error(f"Error exporting logs with attributes: {str(e)}")
            raise Exception(f"Failed to export logs with attributes: {str(e)}")
            
    def export_to_xes_bytes(self, data: Union[pd.DataFrame, EventLog]) -> bytes:
        """Export data to XES format and return as bytes.

        Parameters
        ----------
        data : pd.DataFrame or EventLog
            The data to export, either as a pandas DataFrame or a PM4Py EventLog

        Returns
        -------
        bytes
            The XES file as bytes

        Raises
        ------
        InvalidTypeException
            If data is not a pandas DataFrame or a PM4Py EventLog
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xes') as temp_file:
                temp_path = temp_file.name
                
            # Write data to the temporary file
            if isinstance(data, pd.DataFrame):
                # Convert DataFrame to EventLog
                event_log = pm4py.convert_to_event_log(data)
                pm4py.write_xes(event_log, temp_path)
            elif isinstance(data, EventLog):
                # Write EventLog directly
                pm4py.write_xes(data, temp_path)
            else:
                raise InvalidTypeException("pandas DataFrame or PM4Py EventLog", type(data))
                
            # Read the file as bytes
            with open(temp_path, 'rb') as file:
                xes_bytes = file.read()
                
            # Clean up the temporary file
            os.unlink(temp_path)
            
            return xes_bytes
        except Exception as e:
            logging.error(f"Error exporting to XES bytes: {str(e)}")
            raise Exception(f"Failed to export to XES bytes: {str(e)}")
