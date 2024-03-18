import pandas as pd
from api.custom_error import BadColumnException


def dataframe_to_cases_list(
    df: pd.DataFrame,
    timeLabel: str = "timestamp",
    caseLabel: str = "case",
    eventLabel: str = "event",
) -> list:
    # check that the required columns exist
    required_columns = [timeLabel, caseLabel, eventLabel]
    if not all(col in df.columns for col in required_columns):
        raise BadColumnException(
            "transformations.py ERROR: Selected columns not found in DataFrame"
        )

    # Sort by timestamp
    df = df.sort_values(by=[timeLabel])
    df_grouped = df.groupby(caseLabel)

    cases = []
    for k in df_grouped.groups:
        cases.append(df_grouped.get_group(k)[eventLabel].tolist())
    return cases


def dataframe_to_cases_dict(
    df: pd.DataFrame,
    timeLabel: str = "timestamp",
    caseLabel: str = "case",
    eventLabel: str = "event",
) -> dict:
    # check that the required columns exist
    required_columns = [timeLabel, caseLabel, eventLabel]
    if not all(col in df.columns for col in required_columns):
        raise BadColumnException(
            "transformations.py ERROR: Selected columns not found in DataFrame"
        )

    # Sort by timestamp
    df = df.sort_values(by=[timeLabel])
    df_grouped = df.groupby(caseLabel)

    cases = {}
    for k in df_grouped.groups:
        traces = tuple(df_grouped.get_group(k)[eventLabel].tolist())
        if traces in cases:
            cases[traces] += 1
        else:
            cases[traces] = 1
    return cases
