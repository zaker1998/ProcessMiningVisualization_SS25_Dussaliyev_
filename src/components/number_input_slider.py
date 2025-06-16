import streamlit as st


def number_input_slider(
    label: str,
    min_value: int | float = None,
    max_value: int | float = None,
    value: int | float = None,
    step: int | float = None,
    key: str = None,
    help: str = None,
    ratio: int | list[int] | None = None,
) -> None:
    """Renders a slider and a number input field.

    Parameters
    ----------
    label : str
        The label of the slider and number input field.
    min_value : int | float, optional
        Minimum value of the slider and number input field, by default None
    max_value : int | float, optional
        Maximum value of the slider and number input field, by default None
    value : int | float, optional
        Default value of the slider and number input field, by default None
    step : int | float, optional
        Step size of the slider, by default None
    key : str, optional
        The key of the slider and number input field, by default None
    help : str, optional
        Help text of the slider, by default None
    ratio : int | list[int] | None, optional
        The ratio of the slider and number input field, by default None
    """

    if ratio is None:
        ratio = [5, 2]

    if isinstance(ratio, list):
        ratio = ratio[:2]
        
    # Add a container with custom styling for dark mode compatibility
    with st.container():
        # Show the current value for better visibility
        current_value = st.session_state.get(key, value if value is not None else min_value)
        
        # Display the label with tooltip
        if help:
            st.markdown(f"**{label}** {current_value:.2f}")
        else:
            st.markdown(f"**{label}** {current_value:.2f}")
            
        # Create columns for slider and number input
        silder_column, number_input_column = st.columns(ratio)

        with silder_column:
            st.slider(
                label=f"{label} slider",  # Proper label for accessibility
                min_value=min_value,
                max_value=max_value,
                key=key,
                help=help,
                label_visibility="collapsed",  # Hide the label since we've displayed it above
            )

        with number_input_column:
            # Ensure the value is properly typed to prevent warnings
            current_val = st.session_state[key] if key in st.session_state else value
            if current_val is not None:
                # Convert to float if it's an integer to match the format
                if isinstance(current_val, int) and step is not None and isinstance(step, float):
                    current_val = float(current_val)
            
            st.number_input(
                label=f"{label} input",  # Proper label for accessibility
                min_value=min_value,
                max_value=max_value,
                value=current_val,
                key=f"{key}_text_input",
                on_change=set_session_state,
                args=(key, f"{key}_text_input"),
                format="%.2f" if isinstance(step, float) or isinstance(min_value, float) or isinstance(max_value, float) else "%d",
                label_visibility="collapsed",  # Hide the label since we've displayed it above
            )


def set_session_state(key: str, number_input_key: str) -> None:
    """Updates the session state with the value from the number input.
    
    Parameters
    ----------
    key : str
        The key of the slider
    number_input_key : str
        The key of the number input
    """
    st.session_state[key] = st.session_state[number_input_key]
