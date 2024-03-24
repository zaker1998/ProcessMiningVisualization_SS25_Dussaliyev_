from views.ViewInterface import ViewInterface
import streamlit as st
import pickle


class ExportView(ViewInterface):

    def render(self):
        st.title("Export")
        graph = st.session_state.model.get_graph()
        graph.export_graph("temp/graph", "png")
        format = st.sidebar.selectbox("Export as:", ["PNG", "SVG", "DOT", "Model"])
        if format.lower() == "model":
            self.export_model(st.session_state.model)
        else:
            self.export_graph(graph, format.lower())

        with st.container(border=True):
            st.image("temp/graph.png")

        st.button(
            "Back", type="secondary", on_click=self.navigte_to, args=("Algorithm", True)
        )

    def export_graph(self, graph, format):
        file_name = "temp/graph"
        graph.export_graph(file_name, format)
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
