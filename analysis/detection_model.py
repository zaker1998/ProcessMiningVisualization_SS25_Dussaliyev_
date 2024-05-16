import csv
from streamlit.runtime.uploaded_file_manager import UploadedFile


class DetectionModel:

    def __init__(self, file_type_mappings: dict[str, list[str]] = None):
        """Initializes the DetectionModel.

        Parameters
        ----------
        file_type_mappings : dict[str, list[str]], optional
            A dictionary that maps file types to their suffixes, by default None
        """
        if file_type_mappings is None:
            from config import import_file_types_mapping

            file_type_mappings = import_file_types_mapping

        self.file_type_mappings = file_type_mappings

    def detect_file_type(self, file_path: str | UploadedFile) -> str:
        """Detect the type of a file based on the file extension.

        Parameters
        ----------
        file_path : str | UploadedFile
            The path to the file or the uploaded file

        Returns
        -------
        str
            The detected file type.

        Raises
        ------
        ValueError
            If the file type is not supported
        """
        if isinstance(file_path, UploadedFile):
            file_name = file_path.name
        else:
            file_name = file_path

        for file_type, suffixes in self.file_type_mappings.items():
            for suffix in suffixes:
                if file_name.endswith(suffix):
                    return file_type

        raise ValueError(f"File type not supported for {file_name}")

    def detect_delimiter(self, row: str) -> str:
        """Detect the delimiter of a CSV row.

        Parameters
        ----------
        row : str
            A row of a CSV file

        Returns
        -------
        str
            The detected delimiter. If no delimiter is detected, an empty string is returned.
        """
        detected_delimiter = ""
        try:
            dialect = csv.Sniffer().sniff(row)
            detected_delimiter = dialect.delimiter
        except Exception as e:
            # TODO: use logging
            print(e)

        return detected_delimiter

    # TODO: store supported mime types and the suffixes in a config file, for a more flexible solution
    def detect_mime_type(self, file_path: str) -> str:
        """Detect the mime type of a file.

        Parameters
        ----------
        file_path : str
            The path to the file

        Returns
        -------
        str
            The detected mime type. If the file type is not supported, "text/plain" is returned.
        """

        if file_path.endswith(".png"):
            return "image/png"
        elif file_path.endswith(".svg"):
            return "image/svg"
        elif file_path.endswith(".dot"):
            return "text/plain"
        else:
            return "text/plain"
