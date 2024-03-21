import streamlit as st
from views.Home import Home
from views.HeuristicGraphView import HeuristicGraphView
from views.FuzzyGraphView import FuzzyGraphView
from views.ColumnSelectionView import ColumnSelectionView
from views.ExportView import ExportView


st.set_page_config(
    page_title="Process Mining Tool",
    page_icon=":bar_chart:",
    layout="centered",
)

if "page" not in st.session_state:
    st.session_state.page = "Home"

if st.session_state.page == "Home":
    Home().render()
elif st.session_state.page == "Algorithm":
    if st.session_state.algorithm == "Heuristic Miner":
        HeuristicGraphView().render()
    elif st.session_state.algorithm == "Fuzzy Miner":
        FuzzyGraphView().render()
elif st.session_state.page == "ColumnSelectionView":
    ColumnSelectionView().render()
elif st.session_state.page == "Export":
    ExportView().render()
