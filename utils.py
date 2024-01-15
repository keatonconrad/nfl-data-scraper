import math


def unknown_to_null(x):
    return None if x == "unknown" else x


def to_seconds(min_sec):
    if not isinstance(min_sec, str) and math.isnan(min_sec):
        return None

    min_sec_arr = min_sec.split(":")

    return (int(min_sec_arr[0]) * 60) + int(min_sec_arr[1])
