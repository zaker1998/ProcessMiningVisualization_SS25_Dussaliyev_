class Node:
    def __init__(
        self, id: str | int, label: str = "", data: dict[str, str | int] = None
    ) -> None:
        self.id = id
        if label:
            self.label = label
        else:
            self.label = str(id)
        if data:
            self.data = data
        else:
            self.data = dict()

    def get_label(self) -> str:
        return self.label

    def get_id(self) -> str | int:
        return self.id

    def get_data(self) -> dict[str, str | int]:
        return self.data

    def get_data_from_key(self, key: str) -> str | int:
        return self.data[key]


class Edge:
    def __init__(
        self, source: str | int, destination: str | int, weight: int = 1
    ) -> None:
        self.source = source
        self.destination = destination
        self.weight = weight

    def get_edge(self) -> tuple[str | int, str | int, int]:
        return (self.source, self.destination, self.weight)
