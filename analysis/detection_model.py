import csv
from streamlit.runtime.uploaded_file_manager import UploadedFile


class DetectionModel:

    # TODO: store supported file types and the suffixes in a config file, for a more flexible solution
    def detect_file_type(self, file_path: str | UploadedFile) -> str:
        """Detect the type of a file based on the file extension.

        Parameters
        ----------
        file_path : str | UploadedFile
            The path to the file or the uploaded file

        Returns
        -------
        str
            The detected file type. If the file type is not supported, an empty string is returned.
        """
        if isinstance(file_path, UploadedFile):
            file_name = file_path.name
        else:
            file_name = file_path

        if file_name.endswith(".csv"):
            return "csv"
        elif file_name.endswith(".pickle"):
            return "pickle"
        else:
            # TODO: check use case
            # maybe throw an exception instead of returning an empty string, to handle unsupported file types
            # as selecting a file with an unsupported file type should not be possible
            return ""

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
