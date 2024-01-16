import math
import pandas as pd


def unknown_to_null(x: str):
    return None if x == "unknown" else x


def to_seconds(min_sec: str):
    if not isinstance(min_sec, str) and math.isnan(min_sec):
        return None

    min_sec_arr = min_sec.split(":")

    return (int(min_sec_arr[0]) * 60) + int(min_sec_arr[1])

def get_win_percentage(index: int, team: str, year: str, df: pd.DataFrame):
    if index == 0:
        return None

    wins = sum(game["outcome"] for game in df[team][year][:index])
    return wins / index

def get_win_streak(index: int, team: str, year: str, df: pd.DataFrame):
    if index == 0:
        return 0

    streak = 0
    for game in df[team][year][:index]:
        outcome = game["outcome"]
        if streak >= 1 and outcome == 0 or streak <= -1 and outcome == 1:
            streak = -streak
        elif outcome != 0.5:  # Assuming 0.5 is for ties
            streak = (streak // abs(streak) if streak != 0 else 1) * outcome

    return streak