import {
  Streamlit,
  withStreamlitConnection,
  ComponentProps,
} from "streamlit-component-lib"
import React, { useEffect } from "react"

const Modal: React.FC<ComponentProps> = (props) => {
  const { args } = props
  useEffect(() => {
    Streamlit.setFrameHeight(600)
  }, [])

  return <div>Interactive Graph</div>
}

export default withStreamlitConnection(Modal)
