from views.ViewInterface import ViewInterface
import streamlit as st
import pickle


class ExportView(ViewInterface):
    dpi = 96

    def render(self):
        st.title("Export")
        graph = st.session_state.model.get_graph()
        format = st.sidebar.selectbox("Export as:", ["PNG", "SVG", "DOT", "Model"])
        if format.lower() == "model":
            self.export_model(st.session_state.model)
        else:
            self.export_graph(graph, format.lower())

        graph.export_graph("temp/graph", "png", dpi=self.dpi)

        with st.container(border=True):
            st.image("temp/graph.png")

        st.button(
            "Back", type="secondary", on_click=self.navigte_to, args=("Algorithm", True)
        )

    def export_graph(self, graph, format):
        self.dpi = st.sidebar.number_input("DPI", min_value=50, value=96, step=1)

        file_name = "temp/graph"
        graph.export_graph(file_name, format, dpi=self.dpi)
        with open(file_name + "." + format, "rb") as file:
            st.sidebar.download_button(
                label="Export",
                file_name="graph" + "." + format,
                data=file,
                mime="image/" + format if format != "dot" else "text/plain",
            )

    def export_model(self, model):
        filename = "temp/model.pickle"
        st.sidebar.download_button(
            label="Export",
            file_name="model.pickle",
            data=pickle.dumps(model),
            mime="application/octet-stream",
        )

    def clear(self):
        return
