import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"
import React, { useEffect, useRef, useState } from "react"
import { Graphviz, graphviz } from "d3-graphviz"
import { BaseType, selectAll } from "d3"
import { v4 as uuidv4 } from "uuid"

type nodeClickData = {
  clickId: string
  nodeId: string
}

const InteractiveGraph: React.FC<ComponentProps> = ({ args }) => {
  const dot_source = args["graphviz_string"]
  const key = args["key"]
  const height: number = args["height"]
  const graph_div_ref: React.Ref<HTMLDivElement> = useRef<HTMLDivElement>(null)
  const [nodeClickData, setNodeClickData] = useState<nodeClickData>({
    clickId: "",
    nodeId: "",
  })
  const [width, setWidth] = useState(0)
  const [graphvizInstance, setGraphvizInstance] = useState<Graphviz<
    BaseType,
    any,
    BaseType,
    any
  > | null>(null)

  const [isRendering, setIsRendering] = useState(true)

  function resetGraph() {
    graphviz(".graph").fit(true).resetZoom()
  }

  function bindAfterRender() {
    resetGraph()
    selectAll(".node").on("click", (event) => {
      event.preventDefault()
      const node_id = event.target.__data__.parent.key
      console.log(node_id)
      setNodeClickData({
        clickId: uuidv4(),
        nodeId: node_id,
      })
    })

    setIsRendering(false)
  }

  useEffect(() => {
    const instance = graphviz(graph_div_ref.current).dot(dot_source)
    //.on("layoutStart", () => console.log("Layout start"))
    //.on("layoutEnd", () => console.log("Layout end"))

    setGraphvizInstance(instance)
  }, [dot_source])

  useEffect(() => {
    Streamlit.setFrameHeight(height)

    const onResize = () => {
      if (graph_div_ref.current) {
        setWidth(graph_div_ref.current.clientWidth)
      }
    }

    onResize()
    window.addEventListener("resize", onResize)

    // cleanup
    return () => {
      window.removeEventListener("resize", onResize)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (width === 0 || height === 0) return
    if (graphvizInstance === null) return

    const render_timeout = setTimeout(() => {
      setIsRendering(true)
      console.log(width, height)
      graphvizInstance
        .width(width)
        .height(height)
        .fit(true)
        .zoomScaleExtent([0.1, 100])
        .tweenPaths(false)
        .tweenShapes(false)
        //.on("renderStart", () => console.log("Render start"))
        //.on("renderEnd", () => console.log("Render end"))
        .on("end", bindAfterRender)
        .render()
    }, 100)

    return () => {
      clearTimeout(render_timeout)
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphvizInstance, width, height])

  useEffect(() => {
    Streamlit.setComponentValue(nodeClickData)
  }, [nodeClickData])

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
          margin: "0.25rem",
          border: "none",
          outline: "none",
        }}
      >
        Reset
      </button>

      {isRendering && <div>Loading</div>}
    </div>
  )
}

export default withStreamlitConnection(InteractiveGraph)
