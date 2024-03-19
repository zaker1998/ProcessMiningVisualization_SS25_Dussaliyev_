from abc import ABC, abstractmethod


class ViewInterface(ABC):

    @abstractmethod
    def render(self):
        print("Hello World")
        # raise NotImplementedError("render() method not implemented")
