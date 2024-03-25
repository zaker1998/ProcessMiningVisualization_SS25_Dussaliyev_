import streamlit as st
from views.Home import Home
from views.ColumnSelectionView import ColumnSelectionView
from views.ExportView import ExportView

from config import algorithm_routes, get_algorithm_routes


st.set_page_config(
    page_title="Process Mining Tool",
    page_icon=":bar_chart:",
    layout="wide",
)

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "error" in st.session_state:
    st.error(st.session_state.error)
    del st.session_state.error

if st.session_state.page == "Home":
    Home().render()
elif st.session_state.page == "Algorithm":
    get_algorithm_routes()[st.session_state.algorithm].render()
elif st.session_state.page == "ColumnSelection":
    ColumnSelectionView().render()
elif st.session_state.page == "Export":
    ExportView().render()
