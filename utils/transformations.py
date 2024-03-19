import pandas as pd
from api.custom_error import BadColumnException


def dataframe_to_cases_list(
    df: pd.DataFrame,
    timeLabel: str = "timestamp",
    caseLabel: str = "case",
    eventLabel: str = "event",
) -> list[list[str, ...]]:
    required_columns = [timeLabel, caseLabel, eventLabel]
    if not all(col in df.columns for col in required_columns):
        raise BadColumnException(
            "transformations.py ERROR: Selected columns not found in DataFrame"
        )

    # Sort by timestamp
    df = df.sort_values(by=[timeLabel])

    result = df.groupby(caseLabel)[eventLabel].apply(list).reset_index(name="events")
    return result["events"].tolist()


def cases_list_to_dict(cases_list: list[list[str, ...]]) -> dict[tuple[str, ...], int]:
    cases = {}
    for trace in cases_list:
        trace_tuple = tuple(trace)
        cases[trace_tuple] = cases.get(trace_tuple, 0) + 1
    return cases


def dataframe_to_cases_dict(
    df: pd.DataFrame,
    timeLabel: str = "timestamp",
    caseLabel: str = "case",
    eventLabel: str = "event",
) -> dict[tuple[str, ...], int]:
    cases_list = dataframe_to_cases_list(df, timeLabel, caseLabel, eventLabel)
    return cases_list_to_dict(cases_list)
