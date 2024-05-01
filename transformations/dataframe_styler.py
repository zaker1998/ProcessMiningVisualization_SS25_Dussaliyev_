import pandas as pd


class DataFrameStyler:

    def __init__(self, max_rows_shown: int) -> None:
        """create a new DataframeStyler object

        Parameters
        ----------
        max_rows_shown : int
            the maximum number of rows to show in the styled dataframe
        """
        self.max_rows_shown = max_rows_shown
        self.df = None
        self.column_styles = {}
        self.default_style = ""

    def set_dataframe(self, df: pd.DataFrame):
        """set the dataframe to style

        Parameters
        ----------
        df : _type_
            _description_
        """
        self.df = df

    def set_column_styles(self, column_styles: dict[str, str]):
        """set the column styles for the dataframe

        Parameters
        ----------
        column_styles : dict[str, str]
            a dictionary mapping selected column names to styles
        """
        self.column_styles = column_styles

    def set_default_style(self, default_style: str):
        """set the default style for the dataframe

        Parameters
        ----------
        default_style : str
            the default style for the dataframe
        """
        self.default_style = default_style

    def stlye_df(
        self,
        selected_columns: dict[str, str],
    ) -> pd.DataFrame:
        reduced_df = self.df.head(self.max_rows_shown)
        styled_df = reduced_df.style.apply(
            axis=0,
            func=self.style_df_columns,
            selected_columns=selected_columns,
        )

        return styled_df

    def style_df_columns(self, column, selected_columns):
        if column.name not in selected_columns.values():
            return [self.default_style] * len(column)

        for needed_column, selected_column in selected_columns.items():
            if column.name == selected_column:
                return [
                    self.column_styles.get(needed_column, self.default_style)
                ] * len(column)
