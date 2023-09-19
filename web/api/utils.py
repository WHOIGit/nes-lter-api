import zoneinfo
from django.utils.dateparse import parse_datetime

def parse_datetime_utc(time):
    parsed = parse_datetime(time)
    if not parsed:
        raise ValueError(f"Invalid time {time}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
    return parsed