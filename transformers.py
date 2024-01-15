from datetime import datetime
import pandas as pd
from utils import to_seconds, unknown_to_null

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


def get_teams():
    team_names_df = pd.read_csv("historical-nfl-team-names.csv")
    return {team["Team"]: team["CurrentTeam"] for _, team in team_names_df.iterrows()}


def col_one_dash(df: pd.DataFrame) -> pd.DataFrame:
    df[columns_with_dashes] = df[columns_with_dashes].replace("--", "-", regex=True)
    return df


def col_null_to_zero(df: pd.DataFrame) -> pd.DataFrame:
    df[columns_with_possible_nulls] = (
        df[columns_with_possible_nulls].apply(pd.to_numeric, errors="coerce").fillna(0)
    )
    return df


def col_percent_to_decimal(df: pd.DataFrame) -> pd.DataFrame:
    df[percent_columns] = (
        df[percent_columns].replace("%", "", regex=True).astype(float) / 100
    )
    return df


class Transformer:
    def __init__(self, filename="team_stats.csv"):
        self.df = pd.read_csv(filename).reset_index()
        self.teams = get_teams()

    def separate_team_stats(self):
        separate_teams = {team: {} for team in self.teams}

        for _, row in self.df.iterrows():
            date_obj = datetime.strptime(row["date"], "%B %d, %Y")
            month = date_obj.month
            year = date_obj.year

            if month >= 1 and month <= 6:
                year -= 1

            if year not in separate_teams[row["team"]].keys():
                separate_teams[row["team"]][year] = [row]
            else:
                separate_teams[row["team"]][year].append(row)

        return separate_teams

    def get_win_percentage(self, index, team, year):
        if index == 0:
            return None

        wins = sum(game["outcome"] for game in self.df[team][year][:index])
        return wins / index

    def get_win_streak(self, index, team, year):
        if index == 0:
            return 0

        streak = 0
        for game in self.df[team][year][:index]:
            outcome = game["outcome"]
            if streak >= 1 and outcome == 0 or streak <= -1 and outcome == 1:
                streak = -streak
            elif outcome != 0.5:  # Assuming 0.5 is for ties
                streak = (streak // abs(streak) if streak != 0 else 1) * outcome

        return streak

    def expand_team_stats(self):
        df = col_one_dash(self.df)

        for col in expanded_cols:
            df[expanded_cols[col]] = df[col].str.split("-", expand=True)

            df = df.drop(col, axis=1)

            if "_count" in col:
                df = df.rename(columns={col: col.replace("_count", "")})

        df["away_time_of_possession"] = df["away_time_of_possession"].apply(to_seconds)
        df["home_time_of_possession"] = df["home_time_of_possession"].apply(to_seconds)

        df = df.rename(
            columns={
                "away_rushing": "away_first_downs_rushing",
                "home_rushing": "home_first_downs_rushing",
                "away_passing": "away_first_downs_passing",
                "home_passing": "home_first_downs_passing",
                "away_penalty": "away_first_downs_penalty",
                "home_penalty": "home_first_downs_penalty",
                "away_average_gain": "away_rush_avg",
                "home_average_gain": "home_rush_avg",
                "away_avg_yds/att": "away_pass_att_avg",
                "home_avg_yds/att": "home_pass_att_avg",
            }
        )

        df = col_percent_to_decimal(df)
        df = col_null_to_zero(df)

        self.df = df

    def split_team_stats(self):
        split_objs = []

        for _, row in self.df.iterrows():
            if row["away_score"] > row["home_score"]:
                outcome = 1
            elif row["away_score"] < row["home_score"]:
                outcome = 0
            else:
                outcome = 0.5

            base_obj = {
                col: row[col]
                for col in self.df.columns
                if "away" not in col and "home" not in col
            }

            away_team_obj = {
                **base_obj,
                "outcome": outcome,
                "home_or_away": 1,
                "team": row["away_team"],
                "opponent": row["home_team"],
                "game_index": row["index"],
                **{
                    col.replace("away", "team"): row[col]
                    for col in self.df.columns
                    if "away" in col
                },
                **{
                    col.replace("home", "opp"): row[col]
                    for col in self.df.columns
                    if "home" in col
                },
            }

            home_team_obj = {
                **base_obj,
                "outcome": 1 - outcome,
                "home_or_away": 0,
                "team": row["home_team"],
                "opponent": row["away_team"],
                "game_index": row["index"],
                **{
                    col.replace("home", "team"): row[col]
                    for col in self.df.columns
                    if "home" in col
                },
                **{
                    col.replace("away", "opp"): row[col]
                    for col in self.df.columns
                    if "away" in col
                },
            }

            split_objs.extend([away_team_obj, home_team_obj])

        split_df = pd.DataFrame(split_objs)

        # split_df.drop(split_df.columns[[2, 3, 4]], axis=1, inplace=True)

        split_df["attendance"] = split_df["attendance"].apply(unknown_to_null)

        self.df = split_df

    def stagger_team_stats(self):
        separate_team_stats = self.separate_team_stats()
        separate_teams_list = []

        for team, years in separate_team_stats.items():
            for year, games in years.items():
                for index, game in enumerate(games[:-1]):  # Skip the last game
                    next_game = games[index + 1]
                    game.update(
                        {
                            "outcome": next_game["outcome"],
                            "home_or_away": next_game["home_or_away"],
                            "postseason": next_game["postseason"],
                            "opponent": next_game["opponent"],
                            "date": next_game["date"],
                            "stadium": next_game["stadium"],
                            "current_team": self.teams[game["team"]],
                            "opp_current_team": self.teams[next_game["opponent"]],
                            "team_win_pct": self.get_win_percentage(index, team, year),
                            "opp_win_pct": self.get_win_percentage(
                                index, next_game["opponent"], year
                            ),
                            "team_win_streak": self.get_win_streak(index, team, year),
                            "opp_win_streak": self.get_win_streak(
                                index, next_game["opponent"], year
                            ),
                        }
                    )
                    separate_teams_list.append(game)

        separate_df = pd.DataFrame(separate_teams_list)

        # Rename specific columns
        columns_to_rename = {col: f"prev_{col}" for col in separate_df.columns[9:103]}
        separate_df.rename(columns=columns_to_rename, inplace=True)

        # Reorder column
        cols = [col for col in separate_df.columns if col != "prev_game_index"] + [
            "prev_game_index"
        ]
        separate_df = separate_df[cols]

        self.df = separate_df

    def preprocess_team_stats(self):
        self.df["date"] = pd.to_datetime(self.df["date"])
        ref_date = pd.to_datetime("1978-01-01")
        self.df["recency"] = (self.df["date"] - ref_date).dt.days
        self.df["prev_overtime"] = self.df["prev_overtime"].astype(int)

        self.df.drop(
            [
                "team",
                "opponent",
                "date",
                "stadium",
                "current_team",
                "opp_current_team",
                "prev_game_index",
            ],
            axis=1,
            inplace=True,
        )

    def perform_all_transformations(self):
        self.expand_team_stats()
        self.split_team_stats()
        self.stagger_team_stats()
        self.preprocess_team_stats()
