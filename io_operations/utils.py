import pickle
import pandas as pd
import csv
import os
import base64
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

# TODO: Use docstrings to document the functions not comments


# Loads the class object that was saved as a pickle file. path should include filename
def pickle_load(path: str | UploadedFile) -> object:
    if isinstance(path, UploadedFile):
        load_instance = pickle.load(path)
    else:
        with open(path, "rb") as file:
            load_instance = pickle.load(file)
    return load_instance


def read_csv(filePath: str | UploadedFile, delimiter: str = ",") -> pd.DataFrame:
    df = pd.read_csv(filePath, delimiter=delimiter)
    return df


def read_file(
    filePath: str | UploadedFile, delimiter: str = ","
) -> pd.DataFrame | object:
    if isinstance(filePath, UploadedFile):
        file_name = filePath.name
    else:
        file_name = filePath
    if file_name.endswith(".csv"):
        return read_csv(filePath, delimiter=delimiter)
    elif file_name.endswith(".pickle"):
        return pickle_load(filePath)
    else:
        # TODO: use a custom io exception
        raise ValueError("File format not supported")


def read_img(filePath: str):
    png = open(filePath, "rb").read()
    # https://pmbaumgartner.github.io/streamlitopedia/sizing-and-images.html
    # https://discuss.streamlit.io/t/how-to-show-local-gif-image/3408/2
    # Convert the image to a base64 string to be able to display it in the HTML
    png_base64 = base64.b64encode(png).decode("utf-8")
    return png_base64
