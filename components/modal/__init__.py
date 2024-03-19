import os
import streamlit.components.v1 as components

# Template for the component from https://docs.streamlit.io/library/components/publish and https://github.com/streamlit/component-template/tree/master/template/my_component

_RELEASE = False
_COMPONENT_NAME = "modal"

if not _RELEASE:
    _component_func = components.declare_component(
        _COMPONENT_NAME,
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component(_COMPONENT_NAME, path=build_dir)


def modal(
    key: int | str = None, title: str = "Modal", content: str = "This is a modal"
):
    """Wrapper function for the modal component

    Parameters
    ----------
    key : int | str, optional
        key value for the component. needed if multiple components are displayed on the same page , by default None
    title : str, optional
        Title of the modal, by default "Modal"
    content : str, optional
        Content of the modal, by default "This is a modal"
    """

    component_value = _component_func(key=key, title=title, content=content)
