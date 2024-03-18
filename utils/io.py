import pickle
import pandas as pd
import csv
import os

# TODO: Use docstrings to document the functions not comments


def is_excel_file(file_path: str) -> bool:
    file_format = file_path.split(".")[-1]
    supported_formats = ["xls", "xlsx", "xlsm", "xlsb", "odf", "ods", "odt"]
    return file_format in supported_formats


# Saves the class object as a pickle file. filename is the full path
def pickle_save(class_object: object, filename: str) -> None:
    filePath = filename + ".pickle"
    with open(filePath, "wb") as file:
        pickle.dump(class_object, file)


# Loads the class object that was saved as a pickle file. path should include filename
def pickle_load(path: str) -> object:
    with open(path, "rb") as file:
        load_instance = pickle.load(file)
    return load_instance


def read_csv(filePath: str) -> pd.DataFrame:
    # use csv.Sniffer to detect the delimiter
    with open(filename, "r") as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        delimiter = dialect.delimiter

    # Read the CSV file
    df = pd.read_csv(filename, delimiter=delimiter)
    return df


def read_excel(filePath: str) -> pd.DataFrame:
    return pd.read_excel(filePath)


def read_file(filePath: str) -> pd.DataFrame:
    if filePath.endswith(".csv"):
        return read_csv(filePath)
    elif filePath.endswith(".pickle"):
        return pickle_load(filePath)
    elif is_excel_file(filePath):
        return read_excel(filePath)
    else:
        # TODO: use a custom io exception
        raise ValueError("File format not supported")
