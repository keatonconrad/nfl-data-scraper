from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from datetime import datetime
import pandas as pd
from requests_html import HTMLSession
from utils import toSeconds, unknownToNull
from tqdm import tqdm

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('NFL Data Scraper')

        # Create a central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create a vertical layout
        layout = QVBoxLayout()

        # Add a label and buttons for Transform Options
        layout.addWidget(QLabel("Transform Options"))
        self.add_button(layout, "Perform All Transformations", performAllTransformations)
        self.add_button(layout, "Expand Team Stats", expandTeamStats)
        self.add_button(layout, "Split Team Stats", splitTeamStats)
        self.add_button(layout, "Stagger Team Stats", staggerTeamStats)
        self.add_button(layout, "Preprocess Team Stats", preprocessTeamStats)

        # Add a separator label
        layout.addWidget(QLabel("------"))

        # Add a label and buttons for Scrape Options
        layout.addWidget(QLabel("Scrape Options"))
        self.add_button(layout, "Get All Games", getAllGames)
        self.add_button(layout, "Get Most Recent Games", getMostRecentGames)

        # Set the layout to the central widget
        self.central_widget.setLayout(layout)

    def add_button(self, layout, text, function):
        button = QPushButton(text)
        button.clicked.connect(function)
        layout.addWidget(button)

#############################################################################

def getGame(session, url, player_stats_id, export):
    res = session.get(url)

    team_stats_obj = {}

    game_info = res.html.find('center')[1].text.split('\n')

    if 'AFC' in game_info[0] or 'NFC' in game_info[0] or 'Super Bowl' in game_info[0]:
        if 'Wild Card' in game_info[0]:
            team_stats_obj['postseason'] = 1

        elif 'Divisional' in game_info[0]:
            team_stats_obj['postseason'] = 2

        elif 'Championship' in game_info[0]:
            team_stats_obj['postseason'] = 3

        elif 'Super Bowl' in game_info[0]:
            team_stats_obj['postseason'] = 4

        playoff_add = 1

    else:
        team_stats_obj['postseason'] = 0

        playoff_add = 0

    team_names = game_info[0 + playoff_add]

    team_stats_obj['away_team'] = team_names[:team_names.index(' vs ')]
    team_stats_obj['home_team'] = team_names[(team_names.index(' vs ') + 4):]

    team_stats_obj['date'] = game_info[1 + playoff_add]
    team_stats_obj['stadium'] = game_info[2 + playoff_add]

    if len(game_info) == 4 and 'Attendance' in game_info[3]:
        team_stats_obj['attendance'] = game_info[3][12:].replace(',', '')

    elif len(game_info) == 5 and 'Attendance' in game_info[4]:
        team_stats_obj['attendance'] = game_info[4][12:].replace(',', '')

    else:
        team_stats_obj['attendance'] = 'unknown'

    score_line = res.html.find('.statistics', first=True).text.split('\n')

    if score_line[4] == '5':
        team_stats_obj['overtime'] = 'true'

        team_stats_obj['away_score'] = score_line[12]

        team_stats_obj['home_score'] = score_line[19]

        for i in range(5):
            team_stats_obj[f'away_score_q{i + 1}'] = score_line[7 + i]

        for i in range(5):
            team_stats_obj[f'home_score_q{i + 1}'] = score_line[14 + i]

    else:
        team_stats_obj['overtime'] = 'false'

        team_stats_obj['away_score'] = score_line[10]

        team_stats_obj['home_score'] = score_line[16]

        for i in range(4):
            team_stats_obj[f'away_score_q{i + 1}'] = score_line[6 + i]

        team_stats_obj['away_score_q5'] = '0'
            
        for i in range(5):
            team_stats_obj[f'home_score_q{i + 1}'] = score_line[12 + i]

        team_stats_obj['home_score_q5'] = '0'

    team_stats_sections = res.html.find('#divBox_team', first=True).find('tbody')

    for section in team_stats_sections:
        
        for row in section.find('tr'):

            stats = row.find('td')

            stat_name = stats[0].text

            stat_name = stat_name.lower().replace(' ', '_').replace('_-_', '-').replace('.', '')

            team_stats_obj[f'away_{stat_name}'] = stats[1].text

            team_stats_obj[f'home_{stat_name}'] = stats[2].text

    team_stats_obj['player_stats_id'] = player_stats_id

    player_stats_obj = {}

    player_stats = res.html.find('#divBox_stats', first=True).text.split('\n')

    for stat in player_stats:
        if stat == 'Passing':
            stat_section = 'pass'

        elif stat == 'Rushing':
            stat_section = 'rush'

        elif stat == 'Receiving':
            stat_section = 'rec'

        elif stat == 'Kickoff Returns':
            stat_section = 'kick_ret'

        elif stat == 'Punt Returns':
            stat_section = 'punt_ret'

        elif stat == 'Punting':
            stat_section = 'punt'

        elif stat == 'Kicking':
            stat_section = 'kick'

        elif stat == 'Kickoffs':
            stat_section = 'kickoff'

        elif stat == 'Defense':
            stat_section = 'def'

        elif stat == 'Fumbles':
            stat_section = 'def'

        elif team_stats_obj['away_team'] in stat:
            team = 'away'
            header_flag = True
            stat_headers = []

        elif team_stats_obj['home_team'] in stat:
            team = 'home'
            header_flag = True
            stat_headers = []

        elif '.\xa0' in stat:
            header_flag = False
            player = stat[:(stat.index('.\xa0') - 1)]

            if team == 'away' and player not in player_stats_obj:
                player_stats_obj[player] = {'date': team_stats_obj['date'], 'team': team_stats_obj['away_team'], 'player_stats_id': player_stats_id}

            elif team == 'home' and player not in player_stats_obj:
                player_stats_obj[player] = {'date': team_stats_obj['date'], 'team': team_stats_obj['home_team'], 'player_stats_id': player_stats_id}

            i = 0

        elif stat == 'TeamTeam' or stat == '.':
            header_flag = False
            player = ''

        else:
            if header_flag:
                stat_headers.append(f'{stat_section}_{stat.lower()}')

            else:
                if player != '':
                    player_stats_obj[player][stat_headers[i]] = stat

                    i += 1

    team_df = pd.DataFrame.from_dict([team_stats_obj])

    player_df = pd.DataFrame.from_dict(player_stats_obj, orient='index')

    if export:
        team_df.to_csv('team_stats.csv')

        player_df.to_csv('player_stats.csv')

    return [team_df, player_df]

from concurrent.futures import ThreadPoolExecutor, as_completed

def getGames(start_year, end_year, last_year_start_week, last_year_end_week):
    session = HTMLSession()
    player_stats_id = 0

    # Store data in lists instead of continuous concatenation
    all_team_data = []
    all_player_data = []

    # Function to process each game
    def process_game(game_url):
        url = f'https://www.footballdb.com{game_url}'
        game_stats = getGame(session, url, player_stats_id, False)
        return game_stats

    # Loop through the years
    for year in tqdm(range(start_year, end_year + 1), desc='Years'):
        res = session.get(f'https://www.footballdb.com/games/index.html?lg=NFL&yr={year}')
        game_links = []

        # Determine the range of weeks to process
        week_range = res.html.find('.statistics')
        if year == end_year:
            week_range = week_range[last_year_start_week - 1:last_year_end_week]

        # Collect game URLs
        for week in week_range:
            for game in week.find('tbody tr'):
                game_link = game.find('a', first=True)
                if game_link:
                    game_url = str(game_link.links).replace("{'", '').replace("'}", '')
                    game_links.append(game_url)

        # Parallel processing of games
        with ThreadPoolExecutor() as executor:
            future_to_url = {executor.submit(process_game, url): url for url in game_links}
            for future in tqdm(as_completed(future_to_url), desc='Games', total=len(game_links), leave=False, position=1):
                team_data, player_data = future.result()
                all_team_data.append(team_data)
                all_player_data.append(player_data)

    # Concatenate all data frames outside the loop
    final_team_df = pd.concat(all_team_data, ignore_index=True)
    final_player_df = pd.concat(all_player_data, ignore_index=True)

    return [final_team_df, final_player_df]


def getLastFinishedWeek(year):
    session = HTMLSession()
    response = session.get(f'https://www.footballdb.com/games/index.html?lg=NFL&yr={year}')

    for week_count, week in enumerate(response.html.find('.statistics'), start=1):
        # If any game in the week does not have a link, it's an unplayed game
        if any(game.find('a', first=True) is None for game in week.find('tbody tr')):
            return week_count - 1

    return week_count

def getNFLYear():
    today = datetime.today()
    # If the current month is before June, subtract one year
    return today.year - 1 if today.month < 6 else today.year

def readScrapeInfo():
    with open('info.txt', 'r') as file:
        lines = file.readlines()
        latest_scraped_year = int(lines[0].split('=')[1].strip())
        latest_scraped_week = int(lines[1].split('=')[1].strip())
        return latest_scraped_year, latest_scraped_week

def writeScrapeInfo(current_year, last_finished_week):
    with open('info.txt', 'w') as file:
        file.write(f'latest_scraped_year = {current_year}\n')
        file.write(f'latest_scraped_week = {last_finished_week}\n')

#############################################################################

def getMostRecentGames():
    current_year = getNFLYear()

    last_finished_week = getLastFinishedWeek(current_year)

    scrapeInfo = readScrapeInfo()
    
    recent_dfs = getGames(scrapeInfo[0], current_year, scrapeInfo[1] + 1, last_finished_week)

    writeScrapeInfo(current_year, last_finished_week)

    team_df = pd.read_csv('team_stats.csv')

    player_df = pd.read_csv('player_stats.csv')

    team_df = pd.concat([team_df, recent_dfs[0]], ignore_index = True)

    player_df = pd.concat([player_df, recent_dfs[1]], ignore_index = True)

    team_df.to_csv('team_stats_new.csv', header=False)

    player_df.to_csv('player_stats_new.csv', header=False)


def getAllGames():
    current_year = getNFLYear()

    last_finished_week = getLastFinishedWeek(current_year)

    final_dfs = getGames(1978, current_year, 1, last_finished_week)

    final_dfs[0].to_csv('team_stats.csv')

    final_dfs[1].to_csv('player_stats.csv')

    writeScrapeInfo(current_year, last_finished_week)

#############################################################################

def getTeams():
    team_names = {}

    team_names_df = pd.read_csv('https://raw.githubusercontent.com/ColeBallard/historical-nfl-team-names/main/historical-nfl-team-names.csv')

    for index, team in team_names_df.iterrows():
        team_names[team['Team']] = team['CurrentTeam']

    return team_names

def colOneDash(df):
    columns_with_dashes = [
        'away_punt_returns', 'home_punt_returns', 'away_kickoff_returns', 
        'home_kickoff_returns', 'away_interception_returns', 'home_interception_returns'
    ]

    df[columns_with_dashes] = df[columns_with_dashes].replace('--', '-', regex=True)
    return df


def colNullToZero(df):
    columns_with_possible_nulls = [
        'away_had_blocked', 'home_had_blocked', 'away_int_returns', 'home_int_returns', 
        'away_int_returns_yds', 'home_int_returns_yds', 'away_punts', 'home_punts', 
        'away_punts_avg', 'home_punts_avg', 'away_fg_made', 'home_fg_made', 
        'away_fg_att', 'home_fg_att'
    ]

    df[columns_with_possible_nulls] = df[columns_with_possible_nulls].apply(pd.to_numeric, errors='coerce').fillna(0)
    return df


def colPercentToDecimal(df):
    percent_columns = [
        'away_fourth_downs_percent', 'home_fourth_downs_percent', 
        'away_third_downs_percent', 'home_third_downs_percent'
    ]

    df[percent_columns] = df[percent_columns].replace('%', '', regex=True).astype(float) / 100
    return df


def seperateTeamStats(df):
    seperate_teams = {}

    for team in getTeams():
        seperate_teams[team] = {}

    for index, row in df.iterrows():
        month = datetime.strptime(row['date'], '%B %d, %Y').month

        year = datetime.strptime(row['date'], '%B %d, %Y').year

        if month >= 1 and month <= 6:
            year -= 1

        if year not in seperate_teams[row['team']].keys():
            seperate_teams[row['team']][year] = [row]

        else:
            seperate_teams[row['team']][year].append(row)

    return seperate_teams

def getWinPct(index, team, year, seperate_team_stats):
    wins = 0.0

    if index == 0:
        return None

    for game in seperate_team_stats[team][year][0:index]:
        wins += game['outcome']

    return wins / index

def getWinStreak(index, team, year, seperate_team_stats):
    streak = 0

    if index == 0:
        return 0

    for game in seperate_team_stats[team][year][0:index]:
        if streak >= 1:
            if game['outcome'] == 1:
                streak += 1

            elif game['outcome'] == 0:
                streak = -1

        elif streak <= -1:
            if game['outcome'] == 1:
                streak = 1

            elif game['outcome'] == 0:
                streak -= 1

        else:
            if game['outcome'] == 1:
                streak = 1

            elif game['outcome'] == 0:
                streak = -1
        
    # ties don't affect streak

    return streak


#############################################################################

def expandTeamStats():
    df = pd.read_csv('team_stats.csv')
    export_file = 'expanded_team_stats.csv'
    
    df = df.reset_index()

    expanded_cols = {
        'away_att-comp-int':['away_pass_att', 'away_pass_comp', 'away_pass_int'],
        'home_att-comp-int':['home_pass_att', 'home_pass_comp', 'home_pass_int'],
        'away_sacked-yds_lost':['away_sacked', 'away_sacked_yds_lost'],
        'home_sacked-yds_lost':['home_sacked', 'home_sacked_yds_lost'],
        'away_punts-average':['away_punts', 'away_punts_avg'],
        'home_punts-average':['home_punts', 'home_punts_avg'],
        'away_punt_returns':['away_punt_returns_count', 'away_punt_returns_yds'],
        'home_punt_returns':['home_punt_returns_count', 'home_punt_returns_yds'],
        'away_kickoff_returns':['away_kickoff_returns_count', 'away_kickoff_returns_yds'],
        'home_kickoff_returns':['home_kickoff_returns_count', 'home_kickoff_returns_yds'],
        'away_interception_returns':['away_int_returns', 'away_int_returns_yds'],
        'home_interception_returns':['home_int_returns', 'home_int_returns_yds'],
        'away_penalties-yards':['away_penalties', 'away_penalties_yds'],
        'home_penalties-yards':['home_penalties', 'home_penalties_yds'],
        'away_fumbles-lost':['away_fumbles', 'away_fumbles_lost'],
        'home_fumbles-lost':['home_fumbles', 'home_fumbles_lost'],
        'away_field_goals':['away_fg_made', 'away_fg_att'],
        'home_field_goals':['home_fg_made', 'home_fg_att'],
        'away_third_downs':['away_third_downs_made', 'away_third_downs_att', 'away_third_downs_percent'],
        'home_third_downs':['home_third_downs_made', 'home_third_downs_att', 'home_third_downs_percent'],
        'away_fourth_downs':['away_fourth_downs_made', 'away_fourth_downs_att', 'away_fourth_downs_percent'],
        'home_fourth_downs':['home_fourth_downs_made', 'home_fourth_downs_att', 'home_fourth_downs_percent']
    }

    df = colOneDash(df)

    for col in expanded_cols:
        
        df[expanded_cols[col]] = df[col].str.split('-', expand=True)
        
        df = df.drop(col, axis=1)

        if '_count' in col:
            df = df.rename(columns={col: col.replace('_count', '')})

    df['away_time_of_possession'] = df['away_time_of_possession'].apply(toSeconds)

    df['home_time_of_possession'] = df['home_time_of_possession'].apply(toSeconds)

    df = df.rename(columns={'away_rushing': 'away_first_downs_rushing', 'home_rushing': 'home_first_downs_rushing', 'away_passing': 'away_first_downs_passing', 'home_passing': 'home_first_downs_passing', 'away_penalty': 'away_first_downs_penalty', 'home_penalty': 'home_first_downs_penalty', 'away_average_gain': 'away_rush_avg', 'home_average_gain': 'home_rush_avg', 'away_avg_yds/att': 'away_pass_att_avg', 'home_avg_yds/att': 'home_pass_att_avg'})

    df = colPercentToDecimal(df)

    df = colNullToZero(df)

    cols_list = list(df.columns.values)

    cols_list.pop(cols_list.index('player_stats_id'))

    df = df[cols_list + ['player_stats_id']]

    df.to_csv(export_file)

def splitTeamStats():
    df = pd.read_csv('expanded_team_stats.csv')
    export_file = 'expanded_split_team_stats.csv'

    df = df.reset_index()

    split_objs = []

    df_cols = df.columns.tolist()

    for index, row in df.iterrows():
        away_team_obj = {}
        home_team_obj = {}

        if row['away_score'] > row['home_score']:
            away_team_obj['outcome'] = 1
            home_team_obj['outcome'] = 0

        elif row['away_score'] < row['home_score']:
            away_team_obj['outcome'] = 0
            home_team_obj['outcome'] = 1

        else:
            away_team_obj['outcome'] = 0.5
            home_team_obj['outcome'] = 0.5

        away_team_obj['home_or_away'] = 1
        home_team_obj['home_or_away'] = 0

        for col in df_cols:
            if 'away' not in col and 'home' not in col:
                away_team_obj[col] = row[col]
                home_team_obj[col] = row[col]

            elif col == 'away_team':
                away_team_obj['team'] = row[col]
                home_team_obj['opponent'] = row[col]

            elif col == 'home_team':
                home_team_obj['team'] = row[col]
                away_team_obj['opponent'] = row[col]

            elif 'away' in col:
                away_team_obj[col.replace('away', 'team')] = row[col]
                home_team_obj[col.replace('away', 'opp')] = row[col]

            elif 'home' in col:
                away_team_obj[col.replace('home', 'opp')] = row[col]
                home_team_obj[col.replace('home', 'team')] = row[col]

            else:
                print('error')

        away_team_obj['game_index'] = away_team_obj.pop('index')
        home_team_obj['game_index'] = home_team_obj.pop('index')

        split_objs.append(away_team_obj)
        split_objs.append(home_team_obj)

    split_df = pd.DataFrame.from_dict(split_objs)

    # delete unnamed and pointless columns
    split_df = split_df.drop(split_df.columns[[2, 3, 4]],axis = 1)

    split_df['attendance'] = split_df['attendance'].apply(unknownToNull)

    split_df.to_csv(export_file)

def staggerTeamStats():
    df = pd.read_csv('expanded_split_team_stats.csv')
    team_dict = getTeams()
    export_file = 'staggered_team_stats.csv'
    
    df = df.reset_index()

    seperate_teams = seperateTeamStats(df)

    seperate_teams_list = []

    for team in seperate_teams:

        for year in seperate_teams[team]:

            for index, game in enumerate(seperate_teams[team][year]):

                # -1 to account for 0 index, and -1 to account for no outcome associated with final game stats
                if index <= (len(seperate_teams[team][year]) - 2):
                    game['outcome'] = seperate_teams[team][year][index + 1]['outcome']
                    game['home_or_away'] = seperate_teams[team][year][index + 1]['home_or_away']
                    game['postseason'] = seperate_teams[team][year][index + 1]['postseason']
                    game['opponent'] = seperate_teams[team][year][index + 1]['opponent']
                    game['date'] = seperate_teams[team][year][index + 1]['date']
                    game['stadium'] = seperate_teams[team][year][index + 1]['stadium']

                    game['current_team'] = team_dict[game['team']]
                    game['opp_current_team'] = team_dict[game['opponent']]

                    game['team_win_pct'] = getWinPct(index, team, year, seperate_teams)
                    game['opp_win_pct'] = getWinPct(index, game['opponent'], year, seperate_teams)

                    game['team_win_streak'] = getWinStreak(index, team, year, seperate_teams)
                    game['opp_win_streak'] = getWinStreak(index, game['opponent'], year, seperate_teams)

                    seperate_teams_list.append(game)

    seperate_df = pd.DataFrame(seperate_teams_list)

    for index, col in enumerate(seperate_df.columns.values):
        if index >= 9 and index <= 102:
            seperate_df.rename(columns={seperate_df.columns[index]: f'prev_{col}'},inplace=True)

    seperate_df = seperate_df.drop(seperate_df.columns[1], axis=1)

    # move player stats id and game index columns to end

    cols_list = list(seperate_df.columns.values)

    cols_list.pop(cols_list.index('prev_player_stats_id'))

    cols_list.pop(cols_list.index('prev_game_index'))

    seperate_df = seperate_df[cols_list + ['prev_player_stats_id'] + ['prev_game_index']]

    seperate_df.to_csv(export_file)

def preprocessTeamStats():
    df = pd.read_csv('staggered_team_stats.csv')
    export_file = 'preprocessed_team_stats.csv'
    
    df = df.reset_index()

    df['date'] = pd.to_datetime(df['date'])

    ref_date = pd.to_datetime('1978-01-01')

    df['recency'] = (df['date'] - ref_date).dt.days

    df['prev_overtime'] = df['prev_overtime'].astype(int)

    df = df.drop(['team', 'opponent', 'date', 'stadium', 'current_team', 'opp_current_team', 'prev_player_stats_id', 'prev_game_index'], axis=1)

    df.to_csv(export_file)

def performAllTransformations():
    expandTeamStats()
    splitTeamStats()
    staggerTeamStats()
    preprocessTeamStats()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
