import streamlit as st
import pandas as pd
import time
from functools import wraps


def timed_execution(func):
    """Decorator to measure execution time of functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Store execution time in session state for display
        if "execution_times" not in st.session_state:
            st.session_state.execution_times = {}
        st.session_state.execution_times[func.__name__] = execution_time
        
        return result
    
    return wrapper

def validate_event_log(df):
    """Validates that a dataframe is a proper event log with required columns."""
    # Define sets of acceptable column names for case, event, and time
    case_columns = ["case", "case_id", "case:concept:name"]
    event_columns = ["event", "activity", "concept:name"]
    time_columns = ["time", "timestamp", "time:timestamp"]
    
    # Check if at least one column from each category exists
    has_case = any(col in df.columns for col in case_columns)
    has_event = any(col in df.columns for col in event_columns)
    has_time = any(col in df.columns for col in time_columns)
    
    missing_types = []
    if not has_case:
        missing_types.append("case")
    if not has_event:
        missing_types.append("event")
    if not has_time:
        missing_types.append("time")
    
    if missing_types:
        return False, f"Missing required columns: {', '.join(missing_types)}"
        
    # Check for empty dataframe
    if df.empty:
        return False, "Event log is empty"
        
    # Check for non-datetime time column
    time_col = next((col for col in time_columns if col in df.columns), None)
    try:
        pd.to_datetime(df[time_col])
    except:
        return False, f"Time column '{time_col}' could not be converted to datetime"
        
    return True, "Event log is valid" 