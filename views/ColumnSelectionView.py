import streamlit as st
from views.ViewInterface import ViewInterface
from utils.transformations import dataframe_to_cases_list
from config import algorithm_mappings


class ColumnSelectionView(ViewInterface):

    def predict_columns(self, column_names) -> tuple[str, str, str]:
        time_column = None
        case_column = None
        activity_column = None

        for column in column_names:
            if time_column and case_column and activity_column:
                break

            if time_column is None and (
                "time" in column.lower() or "date" in column.lower()
            ):
                time_column = column
            elif case_column is None and "case" in column.lower():
                case_column = column
            elif activity_column is None and (
                "activity" in column.lower() or "event" in column.lower()
            ):
                activity_column = column

        return time_column, case_column, activity_column

    def render(self):
        if "error" in st.session_state:
            st.error(st.session_state.error)
            del st.session_state.error

        st.title("Column Selection View")
        if "df" not in st.session_state:
            st.session_state.page = "Home"
            st.rerun()

        selection_columns = st.columns([2, 2, 2])

        if (
            "time_column" not in st.session_state
            and "case_column" not in st.session_state
            and "activity_column" not in st.session_state
        ):
            (
                st.session_state.time_column,
                st.session_state.case_column,
                st.session_state.activity_column,
            ) = self.predict_columns(st.session_state.df.columns)

        with selection_columns[0]:
            st.selectbox(
                "Select the time column *",
                st.session_state.df.columns,
                key="time_column",
                index=None,
            )

        with selection_columns[1]:
            st.selectbox(
                "Select the case column *",
                st.session_state.df.columns,
                key="case_column",
                index=None,
            )

        with selection_columns[2]:
            st.selectbox(
                "Select the activity column *",
                st.session_state.df.columns,
                key="activity_column",
                index=None,
            )

        st.multiselect(
            "Select the data columns", st.session_state.df.columns, key="data_columns"
        )

        st.dataframe(
            st.session_state.df,
            use_container_width=True,
            hide_index=True,
            height=500,
        )

        algorithm = st.selectbox("Select the algorithm", [*algorithm_mappings.keys()])

        mine_button = st.button(
            "Mine", type="primary", on_click=self.on_mine_click, args=[algorithm]
        )

    def on_mine_click(self, algorithm):
        if (
            st.session_state.time_column is None
            or st.session_state.case_column is None
            or st.session_state.activity_column is None
        ):
            st.session_state.error = "Please select the time, case and activity columns"
        else:
            st.session_state.algorithm = algorithm_mappings[algorithm]
            self.navigte_to("Algorithm", clean_up=True)

    def clear(self):
        return
