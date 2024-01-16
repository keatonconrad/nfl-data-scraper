from datetime import datetime
import pandas as pd
from requests_html import HTMLSession
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import (
    columns_with_dashes,
    columns_with_possible_nulls,
    percent_columns,
    expanded_cols,
    column_name_mapping,
    GameType,
    label_to_game_type,
    stat_section_mapping,
)
from utils import to_seconds
from models import TeamStat, Game, Session, Team, Stadium, Weather
from dateutil.parser import parse
import re
from pyowm import OWM
import os
from dotenv import load_dotenv
import threading

load_dotenv()


def get_teams():
    team_names_df = pd.read_csv("historical-nfl-team-names.csv")
    return {team["Team"]: team["CurrentTeam"] for _, team in team_names_df.iterrows()}

def parse_capacity(text: str):
    numbers = re.findall(r'[\d,]+', text)
    
    if numbers:
        return int(numbers[0].replace(',', ''))
    return None


class GameGetter:
    def __init__(self):
        self.html_session = HTMLSession()
        self.teams = get_teams()
        self.session = Session()
        self.current_season = self.datetime_to_nfl_season(datetime.today())
        self.last_played_week = self.get_last_played_week()
        self.all_teams = set([t for t in self.session.query(Team).all()])
        self.all_stadiums = set([t for t in self.session.query(Stadium).all()])

        self.owm = OWM(os.environ.get("OWM_API_KEY")).weather_manager()
        self.team_lock = threading.Lock()
        self.stadium_lock = threading.Lock()

    def get_weather(self, stadium: Stadium, date: datetime) -> Weather:
        observation = self.owm.historical_weather_at_coords(
            lat=stadium.latitude, lon=stadium.longitude
        )
        weather_obj = Weather(observation.weather)
        self.session.add(weather_obj)
        return weather_obj

    def datetime_to_nfl_season(self, date: datetime) -> int:
        # If the month is before June, subtract one year
        return date.year - 1 if date.month < 6 else date.year

    def get_player_stats(self, res: HTMLSession, team_stats_obj: dict) -> list[dict]:
        player_stats_obj = {}

        player_stats = res.html.find("#divBox_stats", first=True).text.split("\n")
        header_flag = False
        stat_headers = []
        player = ""
        team = ""

        for stat in player_stats:
            if stat in stat_section_mapping:
                stat_section = stat_section_mapping[stat]

            elif (
                team_stats_obj["away_team"] in stat
                or team_stats_obj["home_team"] in stat
            ):
                team = "away" if team_stats_obj["away_team"] in stat else "home"
                header_flag = True
                stat_headers = []

            elif ".\xa0" in stat:
                header_flag = False
                player = stat[: stat.index(".\xa0") - 1]
                if player not in player_stats_obj:
                    player_stats_obj[player] = {
                        "date": team_stats_obj["date"],
                        "team": team_stats_obj[f"{team}_team"],
                    }
                i = 0

            elif stat == "TeamTeam" or stat == ".":
                header_flag = False
                player = ""

            else:
                if header_flag:
                    stat_headers.append(f"{stat_section}_{stat.lower()}")
                else:
                    if player != "":
                        player_stats_obj[player][stat_headers[i]] = stat
                        i += 1

        return player_stats_obj

    def get_stadium_info(self, stadium: Stadium) -> None:
        stadium_name = (
            "Highmark_Stadium_(New_York)"
            if "Highmark Stadium" in stadium.name
            else stadium.name
        )
        url = f"https://en.wikipedia.org/wiki/{stadium_name.replace(' ', '_')}".split(
            ","
        )[0]

        response = self.html_session.get(url)
        response.raise_for_status()
        infobox = response.html.find(".infobox", first=True)

        for row in infobox.find("tr"):
            header = row.find("th", first=True)
            if header:
                header_text = header.text.strip()

                # Check for city and state
                if header_text in ["Location", "City"]:
                    location = row.find("td", first=True).text.strip()
                    location_parts = location.split(", ")
                    if len(location_parts) >= 2:
                        stadium.city = location_parts[0]
                        stadium.state = location_parts[-1].split("\n")[
                            0
                        ]  # State is usually after the last comma

                # Check for elevation
                if header_text == "Elevation":
                    stadium.elevation = parse_capacity(
                        row.find("td", first=True).text.strip().split("\n")[0]
                    )  # First line usually contains the elevation

                # Check for capacity
                if header_text == "Capacity":
                    stadium.capacity = parse_capacity(
                        row.find("td", first=True).text.strip().split("\n")[0]
                    )  # First line usually contains the capacity

                lat_element = infobox.find(".latitude", first=True)
                if lat_element:
                    stadium.latitude = lat_element.text

                lon_element = infobox.find(".longitude", first=True)
                if lon_element:
                    stadium.longitude = lon_element.text

    def get_or_create_team_by_name(self, name: str) -> Team:
        with self.team_lock:
            team = next(
                (team for team in self.all_teams if team.name in [self.teams[name], name]),
                None,
            )
            if team is None:
                team = Team(name=self.teams[name])
                self.session.add(team)
                # self.session.commit()
                self.all_teams.add(team)

        return team

    def get_or_create_stadium_by_name(self, name: str) -> Stadium:
        with self.stadium_lock:
            stadium = next(
                (
                    stadium
                    for stadium in self.all_stadiums
                    if stadium.name.lower() == name.split(",")[0].strip().lower()
                ),
                None,
            )
            if stadium is None:
                stadium = Stadium(name=name.split(",")[0].strip())
                self.get_stadium_info(stadium)
                self.session.add(stadium)
                # self.session.commit()
                self.all_stadiums.add(stadium)

        return stadium

    def process_stat_value(self, value: str, stat_name: str):
        if stat_name in columns_with_dashes:
            value = value.replace("--", "-")
        if "time_of_possession" in stat_name:
            return to_seconds(value)
        if stat_name in percent_columns:
            return float(value.replace("%", "")) / 100
        if stat_name in columns_with_possible_nulls and value == "":
            return 0
        return value

    def process_and_assign(
        self,
        stat_name: str,
        away_value: str,
        home_value: str,
        away_team_stats: TeamStat,
        home_team_stats: TeamStat,
    ):
        if stat_name in expanded_cols:
            expanded_stat_names = expanded_cols[stat_name]
            away_values = away_value.split("-")
            home_values = home_value.split("-")

            for i, expanded_stat_name in enumerate(expanded_stat_names):
                processed_away_value = self.process_stat_value(
                    away_values[i] if i < len(away_values) else "", expanded_stat_name
                )
                processed_home_value = self.process_stat_value(
                    home_values[i] if i < len(home_values) else "", expanded_stat_name
                )
                setattr(
                    away_team_stats,
                    column_name_mapping[expanded_stat_name],
                    processed_away_value or 0
                )
                setattr(
                    home_team_stats,
                    column_name_mapping[expanded_stat_name],
                    processed_home_value or 0
                )
        else:
            processed_away_value = self.process_stat_value(away_value, stat_name)
            processed_home_value = self.process_stat_value(home_value, stat_name)
            setattr(
                away_team_stats, column_name_mapping[stat_name], processed_away_value
            )
            setattr(
                home_team_stats, column_name_mapping[stat_name], processed_home_value
            )

    def get_team_stats(self, res: HTMLSession) -> dict:
        game = Game()
        away_team_stats = TeamStat()
        home_team_stats = TeamStat()
        self.session.add_all([game, away_team_stats, home_team_stats])
        game.away_team_stats = away_team_stats
        game.home_team_stats = home_team_stats

        week_text = res.html.find(".divheader", first=True).text
        week_match = re.search(r"Week (\d+)", week_text)
        game.week = week_match.group(1) if week_match else None

        game_info = res.html.find("center")[1].text.split("\n")

        playoff_add = 0
        game.game_type = GameType.REGULAR_SEASON

        if any(x in game_info[0] for x in ["AFC", "NFC", "Super Bowl"]):
            for key, value in label_to_game_type.items():
                if key in game_info[0]:
                    game.game_type = value
                    playoff_add = 1
                    break

        team_names = game_info[0 + playoff_add]

        game.away_team = self.get_or_create_team_by_name(
            team_names[: team_names.index(" vs ")]
        )
        game.away_team_stats.team_id = game.away_team.id
        game.home_team = self.get_or_create_team_by_name(
            team_names[(team_names.index(" vs ") + 4) :]
        )
        game.home_team_stats.team_id = game.home_team.id

        game.date = parse(game_info[1 + playoff_add])
        stadium = self.get_or_create_stadium_by_name(game_info[2 + playoff_add])
        game.stadium = stadium
        if game.home_team.stadium is None:
            game.home_team.stadium = stadium

        attendance_index = next(
            (i for i, info in enumerate(game_info) if "Attendance" in info), -1
        )
        if attendance_index != -1:
            game.attendance = game_info[attendance_index][12:].replace(",", "")

        score_line = res.html.find(".statistics", first=True).text.split("\n")

        is_overtime = score_line[4] == "5"
        game.overtime = is_overtime

        if is_overtime:
            away_team_stats.score = score_line[12]
            home_team_stats.score = score_line[19]

            for i in range(5):
                setattr(away_team_stats, f"score_q{i + 1}", score_line[7 + i])
                setattr(home_team_stats, f"score_q{i + 1}", score_line[14 + i])

        else:
            away_team_stats.score = score_line[10]
            home_team_stats.score = score_line[16]

            for i in range(4):
                setattr(away_team_stats, f"score_q{i + 1}", score_line[6 + i])
                setattr(home_team_stats, f"score_q{i + 1}", score_line[12 + i])

        team_stats_sections = res.html.find("#divBox_team", first=True).find("tbody")

        for section in team_stats_sections:
            for row in section.find("tr"):
                stats = row.find("td")
                stat_name = (
                    stats[0]
                    .text.lower()
                    .replace(" ", "_")
                    .replace("_-_", "-")
                    .replace(".", "")
                )

                stat_away_value = stats[1].text
                stat_home_value = stats[2].text

                self.process_and_assign(
                    stat_name,
                    stat_away_value,
                    stat_home_value,
                    away_team_stats,
                    home_team_stats,
                )

        self.session.add_all([game, away_team_stats, home_team_stats, stadium])
        """
        weather = self.get_weather(stadium, game.date)
        
        self.session.add(weather)
        game.weather = weather
        """

        return game, away_team_stats, home_team_stats

    def get_game(self, url: str) -> None:
        res = self.html_session.get(url)
        self.get_team_stats(res)

    def get_games(self, start_year: int, last_year_start_week: int) -> None:
        for year in tqdm(
            range(start_year, self.current_season + 1), desc="Years", position=0
        ):
            res = self.query_game_url()
            game_links = []

            # Determine the range of weeks to process
            week_range = res.html.find(".statistics")

            if year == self.current_season:
                week_range = week_range[last_year_start_week - 1 :]

            # Collect game URLs
            for week in week_range:
                for game in week.find("tbody tr"):
                    game_link = game.find("a", first=True)
                    if game_link:
                        game_url = (
                            str(game_link.links).replace("{'", "").replace("'}", "")
                        )
                        game_links.append(game_url)
                        
            # Parallel processing of games
            with ThreadPoolExecutor() as executor:
                future_to_url = {
                    executor.submit(
                        self.get_game, f"https://www.footballdb.com{url}"
                    ): url
                    for url in game_links
                }
                for future in tqdm(
                    as_completed(future_to_url),
                    desc="Games",
                    total=len(game_links),
                    leave=False,
                    position=1,
                ):
                    future.result()
            try:
                self.session.commit()
            except Exception as e:
                print(e)
                self.session.rollback()
                return

    def query_game_url(self):
        response = self.html_session.get(
            f"https://www.footballdb.com/games/index.html?lg=NFL&yr={self.current_season}",
        )
        response.raise_for_status()
        return response

    def get_last_played_week(self) -> int:
        response = self.query_game_url()

        for week_count, week in enumerate(response.html.find(".statistics"), start=1):
            # If any game in the week does not have a link, it's an unplayed game
            if any(
                game.find("a", first=True) is None for game in week.find("tbody tr")
            ):
                return week_count - 1

        return week_count

    def get_last_scraped_season_and_week(self) -> tuple[int, int]:
        most_recent_game = self.session.query(Game).order_by(Game.date.desc()).first()
        return (
            self.datetime_to_nfl_season(most_recent_game.date.year),
            most_recent_game.week,
        )

    #############################################################################

    def get_most_recent_games(self):
        (
            latest_scraped_year,
            latest_scraped_week,
        ) = self.get_last_scraped_season_and_week()
        self.get_games(latest_scraped_year, latest_scraped_week + 1)

    def get_all_games(self):
        self.get_games(1978, 1)
