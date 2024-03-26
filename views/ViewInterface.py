from abc import ABC, abstractmethod
import streamlit as st


class ViewInterface(ABC):

    @abstractmethod
    def render(self):
        raise NotImplementedError("render() method not implemented")

    def navigte_to(self, page: str, clean_up: bool = False):
        if page == "Home":
            error_message = None
            if "error" in st.session_state:
                error_message = st.session_state.error
            st.session_state.clear()
            if error_message:
                st.session_state.error = error_message
        if clean_up:
            self.clear()
        st.session_state.page = page

    @abstractmethod
    def clear(self):
        return
