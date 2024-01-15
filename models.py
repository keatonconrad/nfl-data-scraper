from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Enum,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from game_getter import GameType

Base = declarative_base()
engine = create_engine("sqlite:///nfl.db")


class Stadium(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String)
    state = Column(String)
    capacity = Column(Integer)
    elevation = Column(Integer)  # in feet


class Team(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    stadium = relationship("Stadium", back_populates="teams")


class Game(Base):
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    home_team_id = Column(Integer, ForeignKey("team.id"))
    home_team = relationship("Team", back_populates="home_games")
    away_team_id = Column(Integer, ForeignKey("team.id"))
    away_team = relationship("Team", back_populates="away_games")
    attendance = Column(Integer)
    overtime = Column(Boolean)
    game_type = Column(Enum(GameType))
    home_team_stats_id = Column(Integer, ForeignKey("team_stat.id"))
    home_team_stats = relationship("TeamStat", uselist=False)
    away_team_stats_id = Column(Integer, ForeignKey("team_stat.id"))
    away_team_stats = relationship("TeamStat", uselist=False)

    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    stadium = relationship("Stadium", back_populates="games")

    home_team_stadium_id = Column(Integer, ForeignKey("stadium.id"))
    home_team_stadium = relationship("Stadium", back_populates="home_games")
    away_team_stadium_id = Column(Integer, ForeignKey("stadium.id"))
    away_team_stadium = relationship("Stadium", back_populates="away_games")


class TeamStat(Base):
    """
    Corresponds to the stats for one team in one game
    """

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