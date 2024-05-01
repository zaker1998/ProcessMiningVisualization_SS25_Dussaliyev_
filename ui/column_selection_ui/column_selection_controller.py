import streamlit as st
from ui.base_ui.base_controller import BaseController
from components.buttons import to_home
from config import algorithm_mappings
from analysis.predictions_model import PredictionModel


class ColumnSelectionController(BaseController):
    max_rows_shown = 200

    def __init__(self, views=None):

        self.predictions_model = PredictionModel()
        if views is None:
            from ui.column_selection_ui.standard_column_selection_view import (
                StandardColumnSelectionView,
            )

            views = [StandardColumnSelectionView()]
        super().__init__(views)

    def get_page_title(self) -> str:
        return "Column Selection"

    def select_view(self):
        if self.selected_algorithm == "":
            # choose other view depending on chosen algorithm
            pass
        else:
            return self.views[0], 0

    def process_session_state(self):
        super().process_session_state()
        if "df" not in st.session_state:
            self.error_message = "Please upload a file first"
            to_home("Home")
            st.rerun()

        if "algorithm_selection" not in st.session_state:
            st.session_state.algorithm_selection = next(iter(algorithm_mappings.keys()))

        self.selected_algorithm = st.session_state.algorithm_selection

        self.df = st.session_state.df

    def predict_columns(self, needed_columns, columns):
        return self.predictions_model.predict_columns(columns, needed_columns)

    def style_df(self, df, column_styles, default_style):
        # TODO: move this method in a model class
        styled_df = df.style.apply(
            axis=0,
            func=self.style_df_columns,
            column_styles=column_styles,
            default_style=default_style,
        )

        return styled_df

    def style_df_columns(self, column, column_styles, default_style):
        # TODO: move this method in a model class
        if column.name not in self.selected_columns.values():
            return [default_style] * len(column)

        for needed_column, selected_column in self.selected_columns.items():
            if column.name == selected_column:
                return [column_styles.get(needed_column, default_style)] * len(column)

    def process_needed_columns(self):
        self.selected_columns = dict()

        # if all columns are None, try to predict them
        if not any(
            [st.session_state.get(column, None) for column in self.needed_columns]
        ):
            predicted_columns = self.predict_columns(
                self.needed_columns, self.df.columns
            )
            # set the predicted columns in the session state
            for predicted_column, needed_column in zip(
                predicted_columns, self.needed_columns
            ):
                st.session_state[needed_column] = predicted_column

        for column in self.needed_columns:
            self.selected_columns[column] = st.session_state.get(column, None)

    def get_needed_columns(self, view):
        self.needed_columns = view.get_needed_columns()

    def run(self, selected_view, index):
        selected_view.display_back_button()
        self.get_needed_columns(selected_view)
        self.process_needed_columns()
        selected_view.display_column_selections(self.df.columns)

        styled_df = self.style_df(
            self.df.head(self.max_rows_shown),
            selected_view.get_column_styles(),
            default_style="",
        )

        selected_view.display_df(styled_df)
        selected_view.display_algorithm_selection([*algorithm_mappings.keys()])
        selected_view.display_mine_button()

    def on_mine_click(self):
        if not all(self.selected_columns.values()):
            st.session_state.error = "Please select a column for all columns"
            st.session_state.page = "ColumnSelection"
            return

        if len(set(self.selected_columns.values())) != len(
            self.selected_columns.values()
        ):
            st.session_state.error = "Please select a different column for each column"
            st.session_state.page = "ColumnSelection"
            return

        st.session_state.algorithm = algorithm_mappings[self.selected_algorithm]
        st.session_state.selected_columns = self.selected_columns
