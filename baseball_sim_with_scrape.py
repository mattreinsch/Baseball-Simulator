import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# Fetch and process the data
page = requests.get("https://www.baseball-reference.com/leagues/MLB/2019-standard-batting.shtml", verify=False)
soup = BeautifulSoup(page.content, 'html.parser')
my_table = soup.find('table')

# Get the column header cells
my_head = my_table.find('thead')
my_head = [cell.text for cell in my_head.find_all('th')]

# Get the rows containing team batting totals
my_table = [row for row in my_table.find_all('tr')]
my_table = [[cell.text for cell in row.find_all('td')] for row in my_table]

# Filter out the empty cells and convert to DataFrame
my_table = [row for row in my_table if row]
stats = pd.DataFrame(data=my_table, columns=my_head[1:])

# Convert numerical columns to float
numerical_cols = ['PA', 'H', '2B', '3B', 'HR', 'BB', 'HBP', 'SF']
stats[numerical_cols] = stats[numerical_cols].apply(pd.to_numeric)

# Calculate singles, walks, and outs
stats['1B'] = stats['H'] - stats[['2B', '3B', 'HR']].sum(axis=1)
stats['WALK'] = stats[['BB', 'HBP']].sum(axis=1)
stats['OUT'] = stats['PA'] - stats[['H', 'WALK']].sum(axis=1)

# Create the needed columns for the 6 outcomes
df_probs = stats[['1B', '2B', '3B', 'HR', 'WALK', 'OUT']]

# Normalize the probabilities
df_probs = df_probs.div(df_probs.sum(axis=1), axis=0)

# Sample 9 players for each team
team1_probs = df_probs.sample(9)
remaining_indices = [ix for ix in df_probs.index if ix not in team1_probs.index]
team2_probs = df_probs.loc[remaining_indices].sample(9)

class Player:
    def __init__(self, probs):
        self.probs = pd.Series(probs) # Player prob distribution
        self.stats = [] # Player at-bat results will be stored here
        
    def at_bat(self):
        outcome = np.random.choice(self.probs.index, p=self.probs.values)
        self.stats.append(outcome)
        return outcome
    
    def OBP(self):
        nonouts = [ab for ab in self.stats if ab != 'OUT']
        return len(nonouts) / len(self.stats) if self.stats else 0
    
    def AVE(self):
        apps = [ab for ab in self.stats if ab != 'WALK']
        hits = [ab for ab in apps if ab != 'OUT']
        return len(hits) / len(apps) if apps else 0
    
    def bases(self, hit_type):
        return {
            'WALK': 1,
            '1B': 1,
            '2B': 2,
            '3B': 3,
            'HR': 4
        }.get(hit_type, 0)
    
    def slugging(self):
        return sum([self.bases(ab) for ab in self.stats]) / len(self.stats) if self.stats else 0

class Team:
    def __init__(self, players):
        self.players = players # List of Player instances
        self.record = [0, 0] # Initial 0-0 record, updated after each game
    
    def update_record(self, win):
        self.record[0 if win else 1] += 1

class Game:
    def __init__(self, teams):
        self.teams = teams
        self.inning = 1
        self.outs = 0
        self.away_or_home = 0
        self.bases = np.array([0, 0, 0])
        self.score = [0, 0]
        self.game_on = True
        self.current_player = [0, 0]
    
    def walker(self):
        self.bases = np.append(self.bases, 0)
        self.bases[0] += 1
        for i in range(3):
            if self.bases[i] == 2:
                self.bases[i] -= 1
                self.bases[i + 1] += 1
        runs = self.bases[-1]
        self.bases = self.bases[:3]
        self.score[self.away_or_home] += runs
    
    def hitter(self, hit_type):
        if hit_type == '1B':
            self.bases = np.insert(self.bases, 0, 1)[:4]
        elif hit_type == '2B':
            self.bases = np.insert(self.bases, 0, [0, 1])[:4]
        elif hit_type == '3B':
            self.bases = np.insert(self.bases, 0, [0, 0, 1])[:4]
        elif hit_type == 'HR':
            self.bases = np.insert(self.bases, 0, [0, 0, 0, 1])[:4]
        runs = self.bases[3:].sum()
        self.bases = self.bases[:3]
        self.score[self.away_or_home] += runs
    
    def handle_at_bat(self):
        player = self.teams[self.away_or_home].players[self.current_player[self.away_or_home]]
        result = player.at_bat()
        if result == 'OUT':
            self.outs += 1
        elif result == 'WALK':
            self.walker()
        else:
            self.hitter(result)
        
        if self.inning >= 9 and ((self.outs >= 3 and self.away_or_home == 0) or self.away_or_home == 1) and self.score[0] != self.score[1]:
            self.game_on = False
        if self.outs >= 3:
            if self.away_or_home == 1:
                self.inning += 1
            self.outs = 0
            self.away_or_home = (self.away_or_home + 1) % 2
            self.bases = np.array([0, 0, 0])
    
    def play_game(self):
        while self.game_on:
            self.handle_at_bat()
        final_score = self.score[:]
        winner = 1 if self.score[1] > self.score[0] else 0
        self.teams[winner].update_record(True)
        self.teams[1-winner].update_record(False)
        return {
            "final_score": final_score,
            "winner": winner
        }

class Simulator:
    def __init__(self, teams):
        self.teams = teams
    
    def simulate(self, its=100):
        game_log = []
        wins = 0
        for _ in range(its):
            game = Game(self.teams)
            result = game.play_game()
            wins += result['winner']
            game_log.append(result)
        print(f"The home team won {wins} out of {its}, for a winning percentage of {wins / its * 100}%!")
        return game_log

# Create players based on sampled probabilities
team1_players = [Player(probs) for probs in team1_probs.values]
team2_players = [Player(probs) for probs in team2_probs.values]

# Create teams
team1 = Team(team1_players)
team2 = Team(team2_players)

# Initialize the simulator with the two teams
simulator = Simulator([team1, team2])

# Run the simulation for 100 games
simulation_results = simulator.simulate(its=100)
