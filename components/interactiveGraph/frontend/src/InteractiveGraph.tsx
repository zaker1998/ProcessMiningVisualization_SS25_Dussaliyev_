import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"
import React, { useEffect, useRef, useState } from "react"
import { graphviz } from "d3-graphviz"
import { selectAll } from "d3"

const InteractiveGraph: React.FC<ComponentProps> = ({ args }) => {
  const dot_source = args["graphviz_string"]
  const key = args["key"]
  const graph_div_ref: React.Ref<HTMLDivElement> = useRef<HTMLDivElement>(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const height: number = 600
  const [size, setSize] = useState({ width: 0, height: height })

  function resetGraph() {
    graphviz(".graph").fit(true).resetZoom()
  }

  function bindAfterRender() {
    resetGraph()

    selectAll(".node").on("click", (event) => {
      event.preventDefault()
      console.log(event.target.__data__.parent.key)
      setSelectedNode(event.target.__data__.parent.key)
    })
  }

  useEffect(() => {
    Streamlit.setFrameHeight(height)

    const onResize = () => {
      if (graph_div_ref.current) {
        setSize({
          width: graph_div_ref.current.clientWidth,
          height: graph_div_ref.current.clientHeight,
        })
      }
    }

    onResize()
    window.addEventListener("resize", onResize)

    // cleanup
    return () => {
      window.removeEventListener("resize", onResize)
    }
  }, [])

  useEffect(() => {
    graphviz(graph_div_ref.current)
      .width(size.width)
      .height(size.height)
      .fit(true)
      //.transition()
      .on("end", bindAfterRender)
      .renderDot(dot_source)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dot_source, size])

  useEffect(() => {
    Streamlit.setComponentValue(selectedNode)
  }, [selectedNode])

  return (
    <div
      id={key}
      style={{
        position: "absolute",
        height: "100%",
        width: "100%",
        backgroundColor: "white",
      }}
    >
      <div
        ref={graph_div_ref}
        className="graph"
        style={{
          position: "absolute",
          height: "100%",
          width: "100%",
        }}
      ></div>
      <button
        onClick={resetGraph}
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          backgroundColor: "#F0F0F0",
          borderRadius: "0.5rem",
          minHeight: "38px",
          padding: "0.25 rem 0.75rem",
          margin: 0,
          border: "none",
          outline: "none",
        }}
      >
        Reset
      </button>
    </div>
  )
}

export default withStreamlitConnection(InteractiveGraph)
