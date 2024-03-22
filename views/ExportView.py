from views.ViewInterface import ViewInterface
import streamlit as st


class ExportView(ViewInterface):

    def render(self):
        st.title("Export")
        graph = st.session_state.graph

        st.graphviz_chart(graph.get_graphviz_string())
        format = st.sidebar.selectbox("Export as:", ["PNG", "SVG", "DOT"])

        self.export_graph(graph, format.lower())

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

    def clear(self):
        del st.session_state.graph
