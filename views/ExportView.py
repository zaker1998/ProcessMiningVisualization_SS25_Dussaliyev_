from views.ViewInterface import ViewInterface
import streamlit as st
import pickle
from components.buttons import navigation_button
from components.PNGViewer import PNGViewer
from utils.io import read_img
from time import time


class ExportView(ViewInterface):
    dpi = 96

    def render(self):
        st.title("Export")
        graph = st.session_state.model.get_graph()
        with st.sidebar:
            format = st.selectbox("Export as:", ["SVG", "PNG", "DOT"])
            format = format.lower()
            self.dpi = st.number_input("DPI", min_value=50, value=96, step=1)
            file_name = "temp/graph"
            graph.export_graph(file_name, format, dpi=self.dpi)

            export_button_col, model_export_button_col = st.columns([1, 1])

            with export_button_col:
                with open(file_name + "." + format, "rb") as file:
                    st.download_button(
                        label="Export",
                        file_name="graph" + "." + format,
                        data=file,
                        mime="image/" + format if format != "dot" else "text/plain",
                        type="primary",
                    )

            with model_export_button_col:
                st.download_button(
                    label="Export Model",
                    file_name="model.pickle",
                    data=pickle.dumps(st.session_state.model),
                    mime="application/octet-stream",
                    type="primary",
                )

        start = time()
        graph.export_graph("temp/graph", "png", dpi=self.dpi)
        end = time()

        print("Time to export graph:", end - start)

        start = time()
        png = read_img("temp/graph.png")
        end = time()

        print("Time to read image:", end - start)

        with st.container(border=True):
            PNGViewer(png, height=600)

        navigation_button("Back", "Algorithm", type="secondary")
