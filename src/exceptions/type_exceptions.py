class InvalidTypeException(Exception):
    """Exception raised when the type of the input is not the expected one."""

    def __init__(self, expected_type, received_type):
        self.expected_type = expected_type
        self.received_type = received_type
        
        # Include MRO information for better debugging
        if hasattr(received_type, '__mro__'):
            mro_info = f", MRO: {received_type.__mro__}"
        else:
            mro_info = ""
            
        self.message = (
            f"Got type '{received_type}'{mro_info}, but expected type '{expected_type}'"
        )
        super().__init__(self.message)


class TypeIsNoneException(Exception):
    """Exception raised when the type of the input is None."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
