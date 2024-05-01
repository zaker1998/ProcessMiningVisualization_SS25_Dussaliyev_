from ui.base_ui.base_view import BaseView
import streamlit as st
from components.buttons import navigation_button
from components.PNGViewer import PNGViewer


class ExportView(BaseView):
    png_height = 600

    def create_layout(self):
        super().create_layout()
        self.png_container = st.container(
            border=True, height=self.png_height + 40
        )  # # add 40 to height to account for padding
        self.back_button_container = st.container()

        with st.sidebar:
            self.export_format_container = st.container()
            self.dpi_container = st.container()
            self.export_button_col, self.model_export_button_col = st.columns([1, 1])

    def display_png(self, png):
        with self.png_container:
            PNGViewer(png, height=self.png_height)

    def display_back_button(self):
        with self.back_button_container:
            navigation_button("Back", "Algorithm", type="secondary")

    def display_export_format(self, formats):
        with self.export_format_container:
            self.export_format = st.selectbox(
                "Export as:", formats, key="export_format"
            )

    def display_dpi_input(self, min_value, value, step):
        with self.dpi_container:
            self.dpi = st.number_input(
                "DPI", min_value=min_value, value=value, step=step, key="dpi"
            )

    def display_export_button(self, file_name, file, mime):
        with self.export_button_col:
            st.download_button(
                label="Export",
                file_name=file_name,
                data=file,
                mime=mime,
                type="primary",
            )

    def display_model_export_button(self, file_name, file):
        with self.model_export_button_col:
            st.download_button(
                label="Export Model",
                file_name=file_name,
                data=file,
                mime="application/octet-stream",
                type="primary",
            )
