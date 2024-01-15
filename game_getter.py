from datetime import datetime
import pandas as pd
from requests_html import HTMLSession
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum


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


class GameGetter:
    def __init__(self):
        self.session = HTMLSession()
        self.last_played_week = self.get_last_played_week()

    @property
    def current_season() -> int:
        today = datetime.today()
        # If the current month is before June, subtract one year
        return today.year - 1 if today.month < 6 else today.year

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

    def get_team_stats(self, res: HTMLSession) -> dict:
        team_stats_obj = {}

        game_info = res.html.find("center")[1].text.split("\n")

        playoff_add = 0
        team_stats_obj["postseason"] = GameType.REGULAR_SEASON.value

        if any(x in game_info[0] for x in ["AFC", "NFC", "Super Bowl"]):
            for key, value in label_to_game_type.items():
                if key in game_info[0]:
                    team_stats_obj["postseason"] = value
                    playoff_add = 1
                    break

        team_names = game_info[0 + playoff_add]

        team_stats_obj["away_team"] = team_names[: team_names.index(" vs ")]
        team_stats_obj["home_team"] = team_names[(team_names.index(" vs ") + 4) :]

        team_stats_obj["date"] = game_info[1 + playoff_add]
        team_stats_obj["stadium"] = game_info[2 + playoff_add]

        attendance_index = next(
            (i for i, info in enumerate(game_info) if "Attendance" in info), -1
        )
        if attendance_index != -1:
            team_stats_obj["attendance"] = game_info[attendance_index][12:].replace(
                ",", ""
            )
        else:
            team_stats_obj["attendance"] = "unknown"

        score_line = res.html.find(".statistics", first=True).text.split("\n")

        is_overtime = score_line[4] == "5"
        team_stats_obj["overtime"] = "true" if is_overtime else "false"

        score_offset = 7 if is_overtime else 6
        team_stats_obj["away_score"] = score_line[score_offset + 5]
        team_stats_obj["home_score"] = score_line[score_offset + 5 + 7]

        for i in range(1, 6):
            team_stats_obj[f"away_score_q{i}"] = (
                score_line[score_offset + i - 1] if i <= 4 or is_overtime else "0"
            )
            team_stats_obj[f"home_score_q{i}"] = (
                score_line[score_offset + i + 6 - 1] if i <= 4 or is_overtime else "0"
            )

        team_stats_sections = res.html.find("#divBox_team", first=True).find("tbody")

        for section in team_stats_sections:
            for row in section.find("tr"):
                stats = row.find("td")
                stat_name = stats[0].text

                stat_name = (
                    stat_name.lower()
                    .replace(" ", "_")
                    .replace("_-_", "-")
                    .replace(".", "")
                )

                team_stats_obj[f"away_{stat_name}"] = stats[1].text
                team_stats_obj[f"home_{stat_name}"] = stats[2].text

        return team_stats_obj

    def get_game(self, session: HTMLSession, url: str) -> tuple[pd.DataFrame]:
        res = session.get(url)

        team_stats = self.get_team_stats(res)
        player_stats = self.get_player_stats(res, team_stats)

        team_df = pd.DataFrame.from_dict([team_stats])
        player_df = pd.DataFrame.from_dict(player_stats, orient="index")

        return team_df, player_df

    def process_game(self, game_url: str) -> tuple[pd.DataFrame]:
        url = f"https://www.footballdb.com{game_url}"
        return self.get_game(self.session, url, False)

    def get_games(
        self, start_year: int, last_year_start_week: int
    ) -> tuple[pd.DataFrame]:
        # Store data in lists instead of continuous concatenation
        all_team_data = []
        all_player_data = []

        # Loop through the years
        for year in tqdm(range(start_year, self.current_season + 1), desc="Years"):
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
                        print("game_url: ", game_url)
                        game_links.append(game_url)

            # Parallel processing of games
            with ThreadPoolExecutor() as executor:
                future_to_url = {
                    executor.submit(self.process_game, url): url for url in game_links
                }
                for future in tqdm(
                    as_completed(future_to_url),
                    desc="Games",
                    total=len(game_links),
                    leave=False,
                    position=1,
                ):
                    team_data, player_data = future.result()
                    all_team_data.append(team_data)
                    all_player_data.append(player_data)

        # Concatenate all data frames outside the loop
        final_team_df = pd.concat(all_team_data, ignore_index=True)
        final_player_df = pd.concat(all_player_data, ignore_index=True)

        return [final_team_df, final_player_df]

    def query_game_url(self):
        return self.session.get(
            f"https://www.footballdb.com/games/index.html?lg=NFL&yr={self.current_season}"
        )

    def get_last_played_week(self):
        response = self.query_game_url()

        for week_count, week in enumerate(response.html.find(".statistics"), start=1):
            # If any game in the week does not have a link, it's an unplayed game
            if any(
                game.find("a", first=True) is None for game in week.find("tbody tr")
            ):
                return week_count - 1

        return week_count

    def read_scrape_info() -> tuple[int, int]:
        with open("info.txt", "r") as file:
            lines = file.readlines()
            latest_scraped_year = int(lines[0].split("=")[1].strip())
            latest_scraped_week = int(lines[1].split("=")[1].strip())
            return latest_scraped_year, latest_scraped_week

    def write_scrape_info(self) -> None:
        with open("info.txt", "w") as file:
            file.write(f"latest_scraped_year = {self.current_season}\n")
            file.write(f"latest_scraped_week = {self.last_finished_week}\n")

    #############################################################################

    def get_most_recent_games(self):
        latest_scraped_year, latest_scraped_week = self.read_scrape_info()

        recent_dfs = self.get_games(latest_scraped_year, latest_scraped_week + 1)

        self.write_scrape_info()

        team_df = pd.read_csv("team_stats.csv")
        player_df = pd.read_csv("player_stats.csv")

        team_df = pd.concat([team_df, recent_dfs[0]], ignore_index=True)
        player_df = pd.concat([player_df, recent_dfs[1]], ignore_index=True)

        team_df.to_csv("team_stats_new.csv", header=False)
        player_df.to_csv("player_stats_new.csv", header=False)

    def get_all_games(self):
        team_stats, player_stats = self.get_games(1978, 1)

        team_stats.to_csv("team_stats.csv")
        player_stats.to_csv("player_stats.csv")

        self.write_scrape_info()
