import streamlit as st
from abc import ABC, abstractmethod
from ui.base_ui.base_view import BaseView
from components.buttons import home_button, navigation_button


class BaseColumnSelectionView(BaseView):

    def create_layout(self):
        super().create_layout()
        self.column_selections_container = st.container()
        self.df_container = st.container()
        self.back_col, _, self.algorithm_column, _, self.mine_col = st.columns(
            [2, 1, 4, 1, 2]
        )

    @abstractmethod
    def get_needed_columns(self) -> list[str]:
        raise NotImplementedError(
            "Method get_needed_columns must be implemented in the child class"
        )

    @abstractmethod
    def get_column_styles(self) -> dict[str, str]:
        raise NotImplementedError(
            "Method get_column_styles must be implemented in the child class"
        )

    @abstractmethod
    def render_column_selections(self, columns: list[str]):
        raise NotImplementedError(
            "Method render_column_selections must be implemented in the child class"
        )

    def display_column_selections(self, columns: list[str]):
        with self.column_selections_container:
            self.render_column_selections(columns)

    def display_algorithm_selection(self, algorithm_selection_options: list[str]):
        with self.algorithm_column:
            algorithm = st.selectbox(
                "Select the algorithm",
                algorithm_selection_options,
                key="algorithm_selection",
            )

    def display_back_button(self):
        with self.back_col:
            st.write("")
            home_button(label="Back", use_container_width=True)

    def display_mine_button(self):
        with self.mine_col:
            st.write("")
            navigation_button(
                label="Mine",
                route="Algorithm",
                use_container_width=True,
                beforeNavigate=self.controller.on_mine_click,
            )

    def display_df(self, styled_df):
        with self.df_container:
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                height=500,
            )
