def InvalidColumnNameException(Exception):
    """Exception raised when the column name is not found in the dataframe."""

    def __init__(self, column_names):
        message = f"Column '{column_names}' not found in the dataset"
        super().__init__(message)


def UnsupportedFileTypeException(Exception):
    """Exception raised when the file type is not supported."""

    def __init__(self, file_type):
        message = f"Unsupported file type '{file_type}'"
        super().__init__(message)


def NotImplementedFileTypeException(Exception):
    """Exception raised when the file type is supported but not implemented."""

    def __init__(self, file_type):
        message = f"File type '{file_type}' not implemented"
        super().__init__(message)
