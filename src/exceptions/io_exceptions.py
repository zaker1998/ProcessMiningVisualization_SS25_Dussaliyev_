class InvalidColumnNameException(Exception):
    """Exception raised when the column name is not found in the dataframe."""

    def __init__(self, column_names):
        self.message = f"Column '{column_names}' not found in the dataset"
        super().__init__(self.message)


class UnsupportedFileTypeException(Exception):
    """Exception raised when a file type is not supported."""

    def __init__(self, file_type: str):
        self.message = f"File type '{file_type}' is not supported."
        super().__init__(self.message)


class NotImplementedFileTypeException(Exception):
    """Exception raised when a file type is not implemented."""

    def __init__(self, file_type: str):
        self.message = f"File type '{file_type}' is not implemented."
        super().__init__(self.message)


class InvalidTypeException(Exception):
    """Exception raised when a type is invalid."""

    def __init__(self, expected_type: str, received_type: type):
        self.message = f"Expected type '{expected_type}', but received '{received_type}'."
        super().__init__(self.message)
