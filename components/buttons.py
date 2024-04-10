import streamlit as st


def home_button(label="Home", route="Home", use_container_width=False) -> None:
    st.button(
        label,
        type="secondary",
        on_click=to_home,
        args=(route,),
        use_container_width=use_container_width,
    )


def to_home(route="Home"):
    error_message = None
    if "error" in st.session_state:
        error_message = st.session_state.error
    st.session_state.clear()
    if error_message:
        st.session_state.error = error_message
    st.session_state.page = route


def navigation_button(
    label,
    route,
    type="primary",
    use_container_width=False,
    beforeNavigate=None,
    args=None,
) -> None:
    if args is None:
        args = ()
    st.button(
        label,
        type=type,
        on_click=navigate_to,
        args=(route, beforeNavigate, *args),
        use_container_width=use_container_width,
    )


def navigate_to(route, beforeNavigate=None, *args):
    st.session_state.page = route
    if beforeNavigate:
        beforeNavigate(*args)
