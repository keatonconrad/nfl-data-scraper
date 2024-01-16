import argparse
from game_getter import GameGetter, get_teams
from models import Session, Game, Team, TeamStat, Stadium
import json
from sqlalchemy.sql import func
from datetime import datetime
from tqdm import tqdm
from sqlalchemy import select
import pandas as pd
import re

game_getter = GameGetter()

teams = get_teams()

def format_team_name(text: str) -> str | None:
    if not text or not isinstance(text, str):
        return None
    split = re.split("[ .]", text)[-1]
    for team in teams.keys():
        if split in team:
            return teams[team]


def find_closest_game(session: Session, game_data: dict) -> Game | None:
    target_date = game_data["date"]
    home_team_keyword = format_team_name(game_data["home_team"])
    away_team_keyword = format_team_name(game_data["away_team"])
    if not home_team_keyword or not away_team_keyword:
        return None
    closest_game = (
        session.query(Game)
        .filter(
            Game.home_team.has(Team.name.contains(home_team_keyword)),
            Game.away_team.has(Team.name.contains(away_team_keyword)),
        )
        .order_by(func.abs(func.extract("epoch", func.age(Game.date, target_date))))
        .first()
    )
    return closest_game


def get_odds():
    with open("nfl_2007.json") as json_file:
        games_data = json.load(json_file)

    session = Session()

    for game in tqdm(games_data[:-1]):
        if not game["date"]:
            continue
        game["date"] = datetime.strptime(str(int(game["date"])), "%Y%m%d")
        closest_game = find_closest_game(session, game)
        if closest_game:
            print(closest_game, game["home_close_ml"], game["away_close_ml"])
            # closest_game.home_moneyline = game["home_close_ml"]
            # closest_game.away_moneyline = game["away_close_ml"]
            # closest_game.over_under = game["open_over_under"]


# session.commit()


def get_all_data():
    session = Session()
    from sqlalchemy.orm import aliased

    # Aliases for Team and TeamStat
    TeamAlias1 = aliased(Team)
    TeamAlias2 = aliased(Team)
    TeamStatAlias1 = aliased(TeamStat)
    TeamStatAlias2 = aliased(TeamStat)

    # Adjusted query
    query = (
        select(Game)
        .join(TeamAlias1, Game.home_team)
        .join(TeamAlias2, Game.away_team)
        .join(TeamStatAlias1, Game.home_team_stats)
        .join(TeamStatAlias2, Game.away_team_stats)
        .join(Stadium, Game.stadium)
    )

    # Execute the query
    results = [i[0] for i in session.execute(query).fetchall()]
    # spread out attributes into columns
    results = [vars(i) for i in results]

    # Convert to Pandas DataFrame
    df = pd.DataFrame(results)
    print(df.columns)

    # Close the session
    session.close()

    print(df.head())


def main():
    parser = argparse.ArgumentParser(description="NFL Data Scraper CLI")
    parser.add_argument("--all", help="Get all games", action="store_true")
    parser.add_argument(
        "--recent", help="Get the most recent games", action="store_true"
    )
    parser.add_argument(
        "--odds",
        help="Get the odds for all games",
    )
    parser.add_argument(
        "--data",
        help="Get all data",
    )

    args = parser.parse_args()

    if args.recent:
        game_getter.get_most_recent_games()
    elif args.odds:
        get_odds()
    elif args.data:
        get_all_data()
    else:
        game_getter.get_all_games()


if __name__ == "__main__":
    main()
