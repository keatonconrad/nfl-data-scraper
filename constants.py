from enum import Enum

expanded_cols = {
    "att-comp-int": ["pass_att", "pass_comp", "pass_int"],
    "att-comp-int": ["pass_att", "pass_comp", "pass_int"],
    "sacked-yds_lost": ["sacked", "sacked_yds_lost"],
    "sacked-yds_lost": ["sacked", "sacked_yds_lost"],
    "punts-average": ["punts", "punts_avg"],
    "punts-average": ["punts", "punts_avg"],
    "punt_returns": ["punt_returns_count", "punt_returns_yds"],
    "punt_returns": ["punt_returns_count", "punt_returns_yds"],
    "kickoff_returns": ["kickoff_returns_count", "kickoff_returns_yds"],
    "kickoff_returns": ["kickoff_returns_count", "kickoff_returns_yds"],
    "interception_returns": ["int_returns", "int_returns_yds"],
    "interception_returns": ["int_returns", "int_returns_yds"],
    "penalties-yards": ["penalties", "penalties_yds"],
    "penalties-yards": ["penalties", "penalties_yds"],
    "fumbles-lost": ["fumbles", "fumbles_lost"],
    "fumbles-lost": ["fumbles", "fumbles_lost"],
    "field_goals": ["fg_made", "fg_att"],
    "field_goals": ["fg_made", "fg_att"],
    "third_downs": [
        "third_downs_made",
        "third_downs_att",
        "third_downs_percent",
    ],
    "third_downs": [
        "third_downs_made",
        "third_downs_att",
        "third_downs_percent",
    ],
    "fourth_downs": [
        "fourth_downs_made",
        "fourth_downs_att",
        "fourth_downs_percent",
    ],
    "fourth_downs": [
        "fourth_downs_made",
        "fourth_downs_att",
        "fourth_downs_percent",
    ],
}

columns_with_dashes = [
    "punt_returns",
    "punt_returns",
    "kickoff_returns",
    "kickoff_returns",
    "interception_returns",
    "interception_returns",
]

columns_with_possible_nulls = [
    "had_blocked",
    "had_blocked",
    "int_returns",
    "int_returns",
    "int_returns_yds",
    "int_returns_yds",
    "punts",
    "punts",
    "punts_avg",
    "punts_avg",
    "fg_made",
    "fg_made",
    "fg_att",
    "fg_att",
]

percent_columns = [
    "fourth_downs_percent",
    "fourth_downs_percent",
    "third_downs_percent",
    "third_downs_percent",
]

# For saving in the database
column_name_mapping = {
    "score": "score",
    "score_q1": "score_q1",
    "score_q2": "score_q2",
    "score_q3": "score_q3",
    "score_q4": "score_q4",
    "score_q5": "score_overtime",
    "first_downs": "first_downs",
    "rushing": "first_downs_rush",
    "passing": "first_downs_pass",
    "penalty": "first_downs_penalty",
    "total_net_yards": "total_net_yards",
    "net_yards_rushing": "rush_net_yards",
    "rushing_plays": "rush_plays",
    "average_gain": "rush_avg_gain",
    "net_yards_passing": "pass_net_yards",
    "gross_yards_passing": "pass_gross_yards",
    "pass_att": "pass_attempts",
    "avg_yds/att": "pass_avg_gain",
    "pass_comp": "pass_completions",
    "pass_int": "pass_interceptions",
    "sacked": "pass_sacked",
    "sacked_yds_lost": "pass_sacked_yards_lost",
    "punts": "punts",
    "punts_avg": "punts_avg",
    "punt_returns_count": "punt_returns",
    "punt_returns_yds": "punt_return_yards",
    "kickoff_returns_count": "kickoff_returns",
    "kickoff_returns_yds": "kickoff_return_yards",
    "int_returns": "interception_returns",
    "int_returns_yds": "interception_return_yards",
    "penalties": "penalties",
    "penalties_yds": "penalty_yards",
    "fumbles": "fumbles",
    "fumbles_lost": "fumbles_lost",
    "fg_made": "field_goals_made",
    "fg_att": "field_goals_attempted",
    "third_downs_made": "third_down_conversions",
    "third_downs_att": "third_down_attempts",
    "third_downs_percent": "third_down_rate",
    "fourth_downs_made": "fourth_down_conversions",
    "fourth_downs_att": "fourth_down_attempts",
    "fourth_downs_percent": "fourth_down_rate",
    "had_blocked": "had_blocked",
    "time_of_possession": "time_of_possession",
    "total_plays": "total_plays",
}


class GameType(Enum):
    REGULAR_SEASON = 0
    WILD_CARD = 1
    DIVISIONAL = 2
    CONFERENCE = 3
    SUPER_BOWL = 4


label_to_game_type = {
    "Regular Season": GameType.REGULAR_SEASON,
    "Wild Card": GameType.WILD_CARD,
    "Divisional": GameType.DIVISIONAL,
    "Conference": GameType.CONFERENCE,
    "Super Bowl": GameType.SUPER_BOWL,
}

# For Player stats
stat_section_mapping = {
    "Passing": "pass",
    "Rushing": "rush",
    "Receiving": "rec",
    "Kickoff Returns": "kick_ret",
    "Punt Returns": "punt_ret",
    "Punting": "punt",
    "Kicking": "kick",
    "Kickoffs": "kickoff",
    "Defense": "def",
    "Fumbles": "fum",
}

team_to_abbr = {
    "Arizona Cardinals": "ARI",
    "Atlanta Falcons": "ATL",
    "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR",
    "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN",
    "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN",
    "Detroit Lions": "DET",
    "Green Bay Packers": "GB",
    "Houston Texans": "HOU",
    "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC",
    "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR",
    "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN",
    "New England Patriots": "NE",
    "New Orleans Saints": "NO",
    "New York Giants": "NYG",
    "New York Jets": "NYJ",
    "Las Vegas Raiders": "LVR",
    "Philadelphia Eagles": "PHI",
    "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF",
    "Seattle Seahawks": "SEA",
    "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN",
    "Washington Commanders": "WAS",
}