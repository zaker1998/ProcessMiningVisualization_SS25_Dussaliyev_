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

  function bindAfterRender() {
    graphviz(".graph").fit(true).resetZoom()

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
  // TODO: learn how transitions work in typescript
  useEffect(() => {
    graphviz(".graph")
      .width(size.width)
      .height(size.height)
      .fit(true)
      //.transition()
      .on("end", bindAfterRender)
      .renderDot(dot_source)
  }, [dot_source, size])

  useEffect(() => {
    Streamlit.setComponentValue(selectedNode)
  }, [selectedNode])

  return (
    <div
      id={key}
      ref={graph_div_ref}
      className="graph"
      style={{
        position: "absolute",
        height: "100%",
        width: "100%",
        backgroundColor: "white",
      }}
    ></div>
  )
}

export default withStreamlitConnection(InteractiveGraph)
