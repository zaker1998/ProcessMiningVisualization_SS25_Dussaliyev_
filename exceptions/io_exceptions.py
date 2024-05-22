class InvalidTypeException(Exception):
    """Exception raised when the type of the input is not the expected one."""

    def __init__(self, expected_type, received_type):
        message = f"Got type '{received_type}', but expected type '{expected_type}'"
        super().__init__(message)


class InvalidModelTypeException(InvalidTypeException):
    """Exception raised when the model type is not the expected one."""

    def __init__(self, expected_model, received_model):
        message = f"Got model of type '{received_model}', but expected model of type '{expected_model}'"
        super().__init__(message)


def InvalidColumnNameException(Exception):
    """Exception raised when the column name is not found in the dataframe."""

    def __init__(self, column_name):
        message = f"Column '{column_name}' not found in the dataset"
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
