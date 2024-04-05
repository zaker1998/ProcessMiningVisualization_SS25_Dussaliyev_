import streamlit as st
from views.ViewInterface import ViewInterface
from utils.transformations import dataframe_to_cases_list
from config import algorithm_mappings


class ColumnSelectionView(ViewInterface):
    max_rows_shown = 200

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
        st.title("Column Selection View")

        if "df" not in st.session_state:
            st.session_state.page = "Home"
            st.session_state.error = "Please upload a file first"
            st.rerun()

        df = st.session_state.df.head(self.max_rows_shown)

        selection_columns = st.columns([2, 2, 2])

        # Try to predict the columns if they are not already set
        if (
            "time_column" not in st.session_state
            and "case_column" not in st.session_state
            and "activity_column" not in st.session_state
        ):
            (
                st.session_state.time_column,
                st.session_state.case_column,
                st.session_state.activity_column,
            ) = self.predict_columns(df)

        with selection_columns[0]:
            st.selectbox(
                "Select the :red[time column] *",
                df.columns,
                key="time_column",
                index=None,
            )

        with selection_columns[1]:
            st.selectbox(
                "Select the :blue[case column] *",
                df.columns,
                key="case_column",
                index=None,
            )

        with selection_columns[2]:
            st.selectbox(
                "Select the :green[activity column] *",
                df.columns,
                key="activity_column",
                index=None,
            )

        st.multiselect(
            "Select the :violet[data columns]", df.columns, key="data_columns"
        )

        styled_df = df.style.apply(
            axis=0,
            func=self.style_df,
        )

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=500,
        )

        back_col, _, algorithm_column, _, mine_col = st.columns([2, 1, 4, 1, 2])

        with algorithm_column:
            algorithm = st.selectbox(
                "Select the algorithm", [*algorithm_mappings.keys()]
            )

        with back_col:
            st.write("")
            back_button = st.button(
                "Back",
                type="secondary",
                on_click=self.navigte_to,
                args=["Home"],
                use_container_width=True,
            )
        with mine_col:
            st.write("")
            mine_button = st.button(
                "Mine",
                type="primary",
                on_click=self.on_mine_click,
                args=[algorithm],
                use_container_width=True,
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

    def style_df(self, col):
        if col.name == st.session_state.time_column:
            return ["background-color: #FF705B" for _ in col]
        elif col.name == st.session_state.case_column:
            return ["background-color: #629AFF" for _ in col]
        elif col.name == st.session_state.activity_column:
            return ["background-color: #57B868" for _ in col]
        elif col.name in st.session_state.data_columns:
            return ["background-color: #C38CFF" for _ in col]

    def clear(self):
        return
