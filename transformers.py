from datetime import datetime
import pandas as pd
from utils import to_seconds, unknown_to_null
from game_getter import GameType
from models import Team, Stadium, TeamStat, Game, Session
import sqlalchemy
from constants import (
    columns_with_dashes,
    columns_with_possible_nulls,
    percent_columns,
    expanded_cols,
)

def get_teams():
    team_names_df = pd.read_csv("historical-nfl-team-names.csv")
    return {team["Team"]: team["CurrentTeam"] for _, team in team_names_df.iterrows()}


def col_one_dash(df: pd.DataFrame) -> pd.DataFrame:
    print(df.columns)
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
        self.filename = filename
        self.teams = get_teams()

        self.session = Session()
        self.all_teams = self.session.query(Team).all()
        self.all_stadiums = self.session.query(Stadium).all()

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
                "home_or_away": 0,
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
                "home_or_away": 1,
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
        return
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
        return
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
        self.df = pd.read_csv(self.filename).reset_index()
        self.seed_database()

        self.expand_team_stats()
        self.split_team_stats()
        self.stagger_team_stats()
        self.preprocess_team_stats()

        self.save_df_to_database()

    def seed_database(self):
        team_stadium = self.df.iloc[:, [4, 7]]
        team_stadium.columns = ['team', 'stadium']
        opponent_stadium = self.df.iloc[:, [5, 7]]
        opponent_stadium.columns = ['team', 'stadium']
        teams = pd.concat([team_stadium, opponent_stadium]).drop_duplicates()

        for _, row in teams.iterrows():
            stadium_exists = self.get_stadium_by_name(row["stadium"]) is not None
            if not stadium_exists:
                stadium = Stadium(name=row["stadium"])
                self.session.add(stadium)
                
            team_exists = self.get_team_by_name(row["team"]) is not None
            if not team_exists:
                team = Team(name=self.teams[row["team"]], stadium=stadium)
                self.session.add(team)
        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError:
            self.session.rollback()
            print("Error: IntegrityError")
            return

    def get_team_by_name(self, name):
        return next((team for team in self.all_teams if team.name == self.teams[name]), None)

    def get_stadium_by_name(self, name):
        return next(
            (stadium for stadium in self.all_stadiums if stadium.name == name),
            None,
        )

    def save_df_to_database(self):
        for _, row in self.df.iterrows():
            home_team_str = row["team"] if row["home_or_away"] == 1 else row["opponent"]
            away_team_str = row["team"] if row["home_or_away"] == 0 else row["opponent"]
            home_team = self.get_team_by_name(home_team_str)
            away_team = self.get_team_by_name(away_team_str)
            home_prefix = "team_" if row["home_or_away"] == 1 else "opp_"
            away_prefix = "opp_" if row["home_or_away"] == 1 else "team_"

            # Create dictionary of stats for the home team
            home_team_stat_dict = {
                self.column_name_mapping[col]: row[home_prefix + col]
                for col in self.column_name_mapping.keys()
                if home_prefix + col in row
            }
            home_team_stat_dict["team_id"] = home_team.id
            home_team_stat = TeamStat(**home_team_stat_dict)

            # Create dictionary of stats for the away team
            away_team_stat_dict = {
                self.column_name_mapping[col]: row[away_prefix + col]
                for col in self.column_name_mapping.keys()
                if away_prefix + col in row
            }
            away_team_stat_dict["team_id"] = away_team.id
            away_team_stat = TeamStat(**away_team_stat_dict)

            game = Game(
                date=row["date"],
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                attendance=row["attendance"],
                overtime=row["overtime"],
                game_type=GameType(int(row["game_type"])),
                home_team_stats=home_team_stat,
                away_team_stats=away_team_stat,
                stadium_id=self.get_stadium_by_name(row["stadium"]).id,
            )
            self.session.add_all([home_team_stat, away_team_stat, game])
        self.session.commit()
