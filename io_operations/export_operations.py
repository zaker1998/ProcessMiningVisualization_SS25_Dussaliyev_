from graphs.visualization.base_graph import BaseGraph
import pickle


class ExportModel:
    # TODO: store supported export formats in a config file, for a more flexible solution
    supported_graph_export_formats = ["png", "svg", "dot"]

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
        TypeError
            If graph is not an instance of BaseGraph
        ValueError
            If the export format is not supported
        """

        if not isinstance(graph, BaseGraph):
            # TODO: Add custom graph exception
            raise TypeError("graph must be an instance of BaseGraph")

        if format.lower() not in self.supported_graph_export_formats:
            # TODO: Add custom io exception for unsupported export format
            raise ValueError(
                f"Unsupported export format: {format}. Supported formats: {self.supported_graph_export_formats}"
            )

        graphviz_graph = graph.get_graphviz_graph()
        export_format = format.lower()

        if export_format == "png":
            graphviz_graph.attr(dpi=str(dpi))
        graphviz_graph.render(filename, format=export_format, cleanup=True)
        if export_format == "png":
            graphviz_graph.attr(dpi="0")

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
