import streamlit as st


def slider(
    label,
    min_value=None,
    max_value=None,
    value=None,
    step=None,
    key=None,
    tooltip=None,
    setValue=None,
):
    value = st.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        step=step,
        key=key,
        help=tooltip,
    )
    if setValue:
        setValue(value)

    return value
