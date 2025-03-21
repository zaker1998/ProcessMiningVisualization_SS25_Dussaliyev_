from graphs.visualization.base_graph import BaseGraph
import pickle
from exceptions.io_exceptions import (
    UnsupportedFileTypeException,
    NotImplementedFileTypeException,
)
from exceptions.type_exceptions import InvalidTypeException
import pm4py
import pandas as pd
from pm4py.objects.log.obj import EventLog
import os


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

    def export_to_xes(self, data, filename: str) -> None:
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

        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to EventLog
            event_log = pm4py.convert_to_event_log(data)
            pm4py.write_xes(event_log, filename)
        elif isinstance(data, EventLog):
            # Write EventLog directly
            pm4py.write_xes(data, filename)
        else:
            raise InvalidTypeException("pandas DataFrame or PM4Py EventLog", type(data))

    def export_to_excel(self, data: pd.DataFrame, filename: str, sheet_name: str = "Sheet1") -> None:
        """Exports a pandas DataFrame to an Excel file

        Parameters
        ----------
        data : pd.DataFrame
            The DataFrame to export
        filename : str
            The name of the file to save to
        sheet_name : str, optional
            The name of the sheet in the Excel file, by default "Sheet1"
        """
        data.to_excel(filename, sheet_name=sheet_name, index=False)

    def export_to_json(self, data: pd.DataFrame, filename: str, orient: str = "records") -> None:
        """Exports a pandas DataFrame to a JSON file

        Parameters
        ----------
        data : pd.DataFrame
            The DataFrame to export
        filename : str
            The name of the file to save to
        orient : str, optional
            The orientation of the JSON file, by default "records"
        """
        data.to_json(filename, orient=orient)

    def export_to_xml(self, data: pd.DataFrame, filename: str) -> None:
        """Exports a pandas DataFrame to an XML file

        Parameters
        ----------
        data : pd.DataFrame
            The DataFrame to export
        filename : str
            The name of the file to save to
        """
        data.to_xml(filename)

    def export_to_parquet(self, data: pd.DataFrame, filename: str) -> None:
        """Exports a pandas DataFrame to a Parquet file

        Parameters
        ----------
        data : pd.DataFrame
            The DataFrame to export
        filename : str
            The name of the file to save to
        """
        data.to_parquet(filename)

    def export_to_csv(self, data: pd.DataFrame, filename: str, delimiter: str = ",") -> None:
        """Exports a pandas DataFrame to a CSV file

        Parameters
        ----------
        data : pd.DataFrame
            The DataFrame to export
        filename : str
            The name of the file to save to
        delimiter : str, optional
            The delimiter to use in the CSV file, by default ","
        """
        data.to_csv(filename, delimiter=delimiter, index=False)
