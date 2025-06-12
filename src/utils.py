import streamlit as st
import hashlib
import pandas as pd
import time
from functools import wraps

def cache_dataframe(func):
    """Decorator to cache pandas dataframes to improve performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a cache key based on function arguments
        key_items = [func.__name__]
        for arg in args:
            if isinstance(arg, pd.DataFrame):
                # For dataframes, use a hash of the first few rows
                key_items.append(hashlib.md5(pd.util.hash_pandas_object(arg.head()).values).hexdigest())
            else:
                key_items.append(str(arg))
                
        for k, v in kwargs.items():
            if isinstance(v, pd.DataFrame):
                key_items.append(f"{k}:{hashlib.md5(pd.util.hash_pandas_object(v.head()).values).hexdigest()}")
            else:
                key_items.append(f"{k}:{v}")
                
        cache_key = hashlib.md5("|".join(key_items).encode()).hexdigest()
        
        # Check if result is in cache
        if cache_key in st.session_state.get("df_cache", {}):
            return st.session_state.df_cache[cache_key]
            
        # Not in cache, compute result
        result = func(*args, **kwargs)
        
        # Store in cache
        if "df_cache" not in st.session_state:
            st.session_state.df_cache = {}
        st.session_state.df_cache[cache_key] = result
        
        return result
    
    return wrapper

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