import zoneinfo

from django.utils.dateparse import parse_datetime

import pandas as pd

def parse_datetime_utc(time):
    parsed = parse_datetime(time)
    if not parsed:
        raise ValueError(f"Invalid time {time}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
    return parsed


def regularize_column_names(df, synonyms):
    new_col_names = {}
    for col in df.columns:
        for preferred, synonyms_list in synonyms.items():
            if col in synonyms_list:
                new_col_names[col] = preferred
                break
        else:
            new_col_names[col] = col
    return df.rename(columns=new_col_names)

