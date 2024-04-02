import pickle
import pandas as pd
import csv
import os
import streamlit as st

# TODO: Use docstrings to document the functions not comments


# Saves the class object as a pickle file. filename is the full path
def pickle_save(class_object: object, filename: str) -> None:
    filePath = filename + ".pickle"
    with open(filePath, "wb") as file:
        pickle.dump(class_object, file)


# Loads the class object that was saved as a pickle file. path should include filename
def pickle_load(path: str) -> object:
    if isinstance(path, st.runtime.uploaded_file_manager.UploadedFile):
        load_instance = pickle.load(path)
    else:
        with open(path, "rb") as file:
            load_instance = pickle.load(file)
    return load_instance


def read_csv(filePath: str) -> pd.DataFrame:
    # use csv.Sniffer to detect the delimiter
    # with open(filePath, "r") as f:
    #    dialect = csv.Sniffer().sniff(f.read(1024))
    #    delimiter = dialect.delimiter

    # Read the CSV file
    df = pd.read_csv(filePath)  # , delimiter=delimiter)
    return df


def read_excel(filePath: str) -> pd.DataFrame:
    return pd.read_excel(filePath)


def read_file(
    filePath: str | st.runtime.uploaded_file_manager.UploadedFile,
) -> pd.DataFrame | object:
    if isinstance(filePath, st.runtime.uploaded_file_manager.UploadedFile):
        file_name = filePath.name
    else:
        file_name = filePath
    if file_name.endswith(".csv"):
        return read_csv(filePath)
    elif file_name.endswith(".pickle"):
        return pickle_load(filePath)
    else:
        # TODO: use a custom io exception
        raise ValueError("File format not supported")
