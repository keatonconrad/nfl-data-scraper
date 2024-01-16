from enum import Enum

expanded_cols = {
    "away_att-comp-int": ["away_pass_att", "away_pass_comp", "away_pass_int"],
    "home_att-comp-int": ["home_pass_att", "home_pass_comp", "home_pass_int"],
    "away_sacked-yds_lost": ["away_sacked", "away_sacked_yds_lost"],
    "home_sacked-yds_lost": ["home_sacked", "home_sacked_yds_lost"],
    "away_punts-average": ["away_punts", "away_punts_avg"],
    "home_punts-average": ["home_punts", "home_punts_avg"],
    "away_punt_returns": ["away_punt_returns_count", "away_punt_returns_yds"],
    "home_punt_returns": ["home_punt_returns_count", "home_punt_returns_yds"],
    "away_kickoff_returns": ["away_kickoff_returns_count", "away_kickoff_returns_yds"],
    "home_kickoff_returns": ["home_kickoff_returns_count", "home_kickoff_returns_yds"],
    "away_interception_returns": ["away_int_returns", "away_int_returns_yds"],
    "home_interception_returns": ["home_int_returns", "home_int_returns_yds"],
    "away_penalties-yards": ["away_penalties", "away_penalties_yds"],
    "home_penalties-yards": ["home_penalties", "home_penalties_yds"],
    "away_fumbles-lost": ["away_fumbles", "away_fumbles_lost"],
    "home_fumbles-lost": ["home_fumbles", "home_fumbles_lost"],
    "away_field_goals": ["away_fg_made", "away_fg_att"],
    "home_field_goals": ["home_fg_made", "home_fg_att"],
    "away_third_downs": [
        "away_third_downs_made",
        "away_third_downs_att",
        "away_third_downs_percent",
    ],
    "home_third_downs": [
        "home_third_downs_made",
        "home_third_downs_att",
        "home_third_downs_percent",
    ],
    "away_fourth_downs": [
        "away_fourth_downs_made",
        "away_fourth_downs_att",
        "away_fourth_downs_percent",
    ],
    "home_fourth_downs": [
        "home_fourth_downs_made",
        "home_fourth_downs_att",
        "home_fourth_downs_percent",
    ],
}

columns_with_dashes = [
    "away_punt_returns",
    "home_punt_returns",
    "away_kickoff_returns",
    "home_kickoff_returns",
    "away_interception_returns",
    "home_interception_returns",
]

columns_with_possible_nulls = [
    "away_had_blocked",
    "home_had_blocked",
    "away_int_returns",
    "home_int_returns",
    "away_int_returns_yds",
    "home_int_returns_yds",
    "away_punts",
    "home_punts",
    "away_punts_avg",
    "home_punts_avg",
    "away_fg_made",
    "home_fg_made",
    "away_fg_att",
    "home_fg_att",
]

percent_columns = [
    "away_fourth_downs_percent",
    "home_fourth_downs_percent",
    "away_third_downs_percent",
    "home_third_downs_percent",
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