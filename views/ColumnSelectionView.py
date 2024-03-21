import streamlit as st
from views.ViewInterface import ViewInterface
from utils.transformations import dataframe_to_cases_list


class ColumnSelectionView(ViewInterface):

    def render(self):
        st.title("Column Selection View")
        if "df" in st.session_state:

            selection_columns = st.columns([2, 2, 2])

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

            st.dataframe(
                st.session_state.df,
                use_container_width=True,
                hide_index=True,
                height=500,
            )

            algorithm = st.selectbox(
                "Select the algorithm", ["Heuristic Miner", "Fuzzy Miner"]
            )

            mine_button = st.button("Mine", type="primary")

            if mine_button:
                cases = dataframe_to_cases_list(
                    st.session_state.df,
                    timeLabel=time_label,
                    caseLabel=case_label,
                    eventLabel=activity_label,
                )

                st.session_state.cases = cases
                st.session_state.algorithm = algorithm
                self.navigte_to("Algorithm", clean_up=True)
                st.rerun()

    def clear(self):
        del st.session_state.df
