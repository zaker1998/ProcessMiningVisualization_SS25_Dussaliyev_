import pickle
import pandas as pd
import csv
import os
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

# TODO: Use docstrings to document the functions not comments


# Saves the class object as a pickle file. filename is the full path
def pickle_save(class_object: object, filename: str) -> None:
    filePath = filename + ".pickle"
    with open(filePath, "wb") as file:
        pickle.dump(class_object, file)


# Loads the class object that was saved as a pickle file. path should include filename
def pickle_load(path: str | UploadedFile) -> object:
    if isinstance(path, UploadedFile):
        load_instance = pickle.load(path)
    else:
        with open(path, "rb") as file:
            load_instance = pickle.load(file)
    return load_instance


def detect_delimiter(filePath: str | UploadedFile) -> str:
    if isinstance(filePath, UploadedFile):
        dialect = csv.Sniffer().sniff(filePath.readline().decode("utf-8"))
        filePath.seek(0)
    else:
        with open(filePath, "r") as f:
            dialect = csv.Sniffer().sniff(f.readline())

    delimiter = dialect.delimiter
    return delimiter


def read_csv(filePath: str | UploadedFile, delimiter: str = ",") -> pd.DataFrame:
    df = pd.read_csv(filePath, delimiter=delimiter)
    return df


def read_excel(filePath: str) -> pd.DataFrame:
    return pd.read_excel(filePath)


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
