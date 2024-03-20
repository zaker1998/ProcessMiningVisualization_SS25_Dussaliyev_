import streamlit as st
from views.ViewInterface import ViewInterface
from utils.transformations import dataframe_to_cases_list


class ColumnSelectionView(ViewInterface):

    def render(self):
        st.write("Column Selection View")
        if "df" in st.session_state:

            selection_columns = st.columns(3)

            with selection_columns[0]:

                time_label = st.selectbox(
                    "Select the time column", st.session_state.df.columns
                )

            with selection_columns[1]:
                case_label = st.selectbox(
                    "Select the case column", st.session_state.df.columns
                )

            with selection_columns[2]:
                activity_label = st.selectbox(
                    "Select the activity column", st.session_state.df.columns
                )

            st.write(st.session_state.df)

            mine_button = st.button("Mine")
            if mine_button:
                cases = dataframe_to_cases_list(
                    st.session_state.df,
                    timeLabel=time_label,
                    caseLabel=case_label,
                    eventLabel=activity_label,
                )

                st.session_state.cases = cases
                st.session_state.page = "Algorithm"
                st.rerun()
