from abc import ABC, abstractmethod


class ViewInterface(ABC):

    @abstractmethod
    def render(self):
        raise NotImplementedError("render() method not implemented")
