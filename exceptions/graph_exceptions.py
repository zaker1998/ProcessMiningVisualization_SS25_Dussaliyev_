class DuplicateNodeException(Exception):

    def __init__(self, node):
        self.message = f"Node '{node}' already exists in the graph."
        super().__init__(self.message)


class DuplicateEdgeException(Exception):

    def __init__(self, source, target):
        self.message = f"Edge from {source} to {target} already exists."
        super().__init__(self.message)


class NodeDoesNotExistException(Exception):

    def __init__(self, node):
        self.message = f"Node '{node}' does not exist in the graph."
        super().__init__(self.message)


class EdgeDoesNotExistException(Exception):

    def __init__(self, source, target):
        self.message = f"Edge from {source} to {target} does not exist."
        super().__init__(self.message)


class InvalidNodeNameException(Exception):

    def __init__(self, node):
        self.message = f"Node '{node}' is not a valid node name."
        super().__init__(self.message)
