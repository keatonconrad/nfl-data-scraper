from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Enum,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from constants import GameType, team_to_abbr
import re
from requests_html import HTMLSession

Base = declarative_base()
engine = create_engine("postgresql://postgres:postgres@10.0.0.10:5432/nfl-data")


def parse_numbers(text: str) -> int | None:
    numbers = re.findall(r"[\d,]+", text)

    if numbers:
        return int(numbers[0].replace(",", ""))
    return None


class Stadium(Base):
    __tablename__ = "stadium"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    city = Column(String)
    state = Column(String)
    capacity = Column(Integer)
    elevation = Column(Integer)  # in feet
    latitude = Column(String)
    longitude = Column(String)
    teams = relationship("Team", back_populates="stadium")
    games = relationship("Game", back_populates="stadium")

    def __repr__(self):
        return f"<Stadium(name={self.name}, city={self.city}, state={self.state})>"

    def get_info(self, html_session: HTMLSession) -> None:
        stadium_name = (
            "Highmark_Stadium_(New_York)"
            if "Highmark Stadium" in self.name
            else self.name
        )
        url = f"https://en.wikipedia.org/wiki/{stadium_name.replace(' ', '_')}".split(
            ","
        )[0]

        response = html_session.get(url)
        response.raise_for_status()
        infobox = response.html.find(".infobox", first=True)
        if not infobox:
            return

        for row in infobox.find("tr"):
            header = row.find("th", first=True)
            if header:
                header_text = header.text.strip()

                # Check for city and state
                if header_text in ["Location", "City"]:
                    location = row.find("td", first=True).text.strip()
                    location_parts = location.split(", ")
                    if len(location_parts) >= 2:
                        self.city = location_parts[0]
                        self.state = location_parts[-1].split("\n")[
                            0
                        ]  # State is usually after the last comma

                # Check for elevation
                if header_text == "Elevation":
                    self.elevation = parse_numbers(
                        row.find("td", first=True).text.strip().split("\n")[0]
                    )  # First line usually contains the elevation

                # Check for capacity
                if header_text == "Capacity":
                    self.capacity = parse_numbers(
                        row.find("td", first=True).text.strip().split("\n")[0]
                    )  # First line usually contains the capacity

                lat_element = infobox.find(".latitude", first=True)
                if lat_element:
                    self.latitude = lat_element.text

                lon_element = infobox.find(".longitude", first=True)
                if lon_element:
                    self.longitude = lon_element.text


class Team(Base):
    __tablename__ = "team"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    abbreviation = Column(String, unique=True)
    
    def __init__(self, name: str) -> None:
        self.name = name
        self.abbreviation = team_to_abbr[name] if name in team_to_abbr else None

    stadium = relationship("Stadium", back_populates="teams")
    home_games = relationship("Game", foreign_keys="Game.home_team_id")
    away_games = relationship("Game", foreign_keys="Game.away_team_id")


class Game(Base):
    __tablename__ = "game"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    week = Column(Integer)  # Week of the season
    home_team_id = Column(Integer, ForeignKey("team.id"))
    away_team_id = Column(Integer, ForeignKey("team.id"))
    attendance = Column(Integer)
    overtime = Column(Boolean)
    game_type = Column(Enum(GameType))
    home_team_stats_id = Column(Integer, ForeignKey("team_stat.id"))
    away_team_stats_id = Column(Integer, ForeignKey("team_stat.id"))
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    weather_id = Column(Integer, ForeignKey("weather.id"))
    home_moneyline = Column(Integer)
    away_moneyline = Column(Integer)
    over_under = Column(Float)

    UniqueConstraint(
        "date", "home_team_id", "away_team_id", name="unique_game_constraints"
    )

    home_team = relationship(
        "Team", foreign_keys=[home_team_id], back_populates="home_games"
    )
    away_team = relationship(
        "Team", foreign_keys=[away_team_id], back_populates="away_games"
    )
    home_team_stats = relationship(
        "TeamStat", foreign_keys=[home_team_stats_id], uselist=False
    )
    away_team_stats = relationship(
        "TeamStat", foreign_keys=[away_team_stats_id], uselist=False
    )
    stadium = relationship("Stadium", foreign_keys=[stadium_id], back_populates="games")
    weather = relationship("Weather", foreign_keys=[weather_id], uselist=False)


class TeamStat(Base):
    """
    Corresponds to the stats for one team in one game
    """

    __tablename__ = "team_stat"

    id = Column(Integer, primary_key=True)
    score = Column(Integer)
    score_q1 = Column(Integer)
    score_q2 = Column(Integer)
    score_q3 = Column(Integer)
    score_q4 = Column(Integer)
    score_overtime = Column(Integer)
    first_downs = Column(Integer)
    first_downs_rush = Column(Integer)
    first_downs_pass = Column(Integer)
    first_downs_penalty = Column(Integer)
    total_net_yards = Column(Integer)
    rush_net_yards = Column(Integer)
    rush_plays = Column(Integer)
    rush_avg_gain = Column(Float)
    pass_net_yards = Column(Integer)
    pass_completions = Column(Integer)
    pass_attempts = Column(Integer)
    pass_completion_rate = Column(Float)
    pass_interceptions = Column(Integer)
    pass_sacked = Column(Integer)
    pass_sacked_yards_lost = Column(Integer)
    pass_gross_yards = Column(Integer)
    pass_avg_gain = Column(Float)
    punts = Column(Integer)
    punt_avg = Column(Float)
    punts_blocked = Column(Integer)
    punt_returns = Column(Integer)
    punt_return_yards = Column(Integer)
    kickoff_returns = Column(Integer)
    kickoff_return_yards = Column(Integer)
    interception_returns = Column(Integer)
    interception_return_yards = Column(Integer)
    penalties = Column(Integer)
    penalty_yards = Column(Integer)
    fumbles = Column(Integer)
    fumbles_lost = Column(Integer)
    field_goals_attempted = Column(Integer)
    field_goals_made = Column(Integer)
    third_down_conversions = Column(Integer)
    third_down_rate = Column(Float)
    third_down_attempts = Column(Integer)
    fourth_down_conversions = Column(Integer)
    fourth_down_attempts = Column(Integer)
    fourth_down_rate = Column(Float)
    total_plays = Column(Integer)
    avg_gain = Column(Float)
    time_of_possession = Column(Integer)


class Weather(Base):
    __tablename__ = "weather"
    id = Column(Integer, primary_key=True)
    humidity = Column(Float)
    wind_speed = Column(Float)
    wind_deg = Column(Float)
    wind_gust = Column(Float)
    clouds = Column(Float)
    rain = Column(Float)
    snow = Column(Float)
    precipitation = Column(Float)
    weather_code = Column(Integer)
    weather_main = Column(String)
    pressure = Column(Float)
    visibility = Column(Float)
    temp_low = Column(Float)
    temp_high = Column(Float)


# set up sessionmaker
Session = sessionmaker(bind=engine)

# create all
Base.metadata.create_all(engine)
