import streamlit as st
import streamlit.components.v1 as components
import base64


def PNGViewer(png_path: str, height: int = 600):
    png = open(png_path, "rb").read()

    # https://pmbaumgartner.github.io/streamlitopedia/sizing-and-images.html
    # Convert the image to a base64 string to be able to display it in the HTML
    png_base64 = base64.b64encode(png).decode("utf-8")

    html = f"""
    <div style="display: flex; justify-content: center; height:{height}px; width:100%;background-color:white;">
    <img src="data:image/png;base64,{png_base64}" alt="png" style="max-width:99%; max-height:98%;object-fit:contain">
    </div>
    """
    components.html(html, height=height)
