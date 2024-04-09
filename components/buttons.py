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
