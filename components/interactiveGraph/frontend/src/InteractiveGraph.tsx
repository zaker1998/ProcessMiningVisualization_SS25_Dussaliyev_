import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"
import React, { useEffect } from "react"
import { graphviz } from "d3-graphviz"

const InteractiveGraph: React.FC<ComponentProps> = ({ args }) => {
  const dot_source = args["graphviz_string"]
  const key = args["key"]

  const height = 600

  useEffect(() => {
    Streamlit.setFrameHeight(height)
  }, [])

  useEffect(() => {
    graphviz(".graph")
      //.width(2 * height)
      .height(height)
      .fit(true)
      .zoom(true)
      .renderDot(dot_source)
  }, [dot_source])

  return (
    <div
      key={key}
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
