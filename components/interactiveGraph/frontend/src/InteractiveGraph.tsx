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

  const [size, setSize] = useState({ width: 0, height: 0 })

  // maybe later needed if area inside node works for click
  //const [selctedNode, setSelectedNode] = useState<string>("")

  function bindOnNodeClick() {
    //get node from "event.currentTarget"

    selectAll(".node").on("click", (event) => {
      event.preventDefault()
      console.log(event.target.__data__.parent.key)

      Streamlit.setComponentValue(event.target.__data__.parent.key)
    })
  }

  useEffect(() => {
    Streamlit.setFrameHeight(600)

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

    return () => {
      window.removeEventListener("resize", onResize)
    }
  }, [])

  useEffect(() => {
    graphviz(".graph")
      .width(size.width)
      .height(size.height)
      .fit(true)
      .on("end", bindOnNodeClick)
      .renderDot(dot_source)
  }, [dot_source, size])

  return (
    <div
      id={key}
      ref={graph_div_ref}
      className="graph"
      style={{
        position: "absolute",
        height: "100%",
        width: "100%",
      }}
    ></div>
  )
}

export default withStreamlitConnection(InteractiveGraph)
