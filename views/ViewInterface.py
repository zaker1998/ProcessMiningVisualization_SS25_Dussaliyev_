from abc import ABC, abstractmethod
import streamlit as st


class ViewInterface(ABC):

    @abstractmethod
    def render(self):
        raise NotImplementedError("render() method not implemented")
