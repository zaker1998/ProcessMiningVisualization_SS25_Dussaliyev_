import streamlit as st
from ui.home_ui.home_controller import HomeController
from views.ColumnSelectionView import ColumnSelectionView
from views.ExportView import ExportView
from views.AlgorithmDocView import AlgorithmDocView

from config import algorithm_routes, get_algorithm_view


st.set_page_config(
    page_title="Process Mining Tool",
    page_icon=":bar_chart:",
    layout="wide",
)

if "page" not in st.session_state:
    st.session_state.page = "Home"

if st.session_state.page == "Home":
    HomeController().start()
elif st.session_state.page == "Algorithm":
    get_algorithm_view(st.session_state.algorithm).start()
elif st.session_state.page == "ColumnSelection":
    ColumnSelectionView().render()
elif st.session_state.page == "Export":
    ExportView().render()
elif st.session_state.page == "Documentation":
    AlgorithmDocView().render()
