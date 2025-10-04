# Baseball-Simulator

![Baseball-Simulator](baseball_sim.jpg)

## Introduction

Welcome to an exploration of a baseball simulation script written in Python! This script models the outcomes of baseball games using probability distributions for player performance. It comprises classes for players, teams, games, and a simulator to run multiple games. This article will break down the script step-by-step, providing insights into how it works and how you can use it to simulate baseball games.

## Player Class

The `Player` class represents individual baseball players with distinct probabilities for different outcomes like singles, doubles, walks, and outs.

### Initialization

```python
class Player:
    def __init__(self, probs):
        self.probs = pd.Series(probs) # Player probability distribution
        self.stats = [] # Player at-bat results will be stored here
```
probs: A dictionary of probabilities for various outcomes (e.g., single, double, etc.).
stats: A list to store the outcomes of each at-bat.

### at_bat Method
Simulates a single at-bat by randomly choosing an outcome based on the player's probability distribution and records the outcome.

```python
def at_bat(self):
    outcome = np.random.choice(self.probs.index, p=self.probs.values)
    self.stats.append(outcome)
    return outcome
```

### OBP Method
Calculates On-Base Percentage (OBP), the ratio of times the player gets on base to total at-bats.

```python
def OBP(self):
    nonouts = [ab for ab in self.stats if ab != 'OUT']
    return 1.0 * len(nonouts) / len(self.stats)
```

### AVE Method
Calculates Batting Average (AVE), the ratio of hits (excluding walks and outs) to total at-bats.

```python
def AVE(self):
    apps = [ab for ab in self.stats if ab != 'WALK']
    hits = [ab for ab in apps if ab != 'OUT']
    return 1.0 * len(hits) / len(apps)
```

### bases Method
Returns the number of bases for a given hit type.

```python
def bases(self, hit_type):
    if hit_type in ['WALK', '1B']:
        return 1
    elif hit_type == '2B':
        return 2
    elif hit_type == '3B':
        return 3
    elif hit_type == 'HR':
        return 4
    else:
        return 0
```

### slugging Method
Calculates the slugging percentage, the average number of bases per at-bat.

```python
def slugging(self):
    return sum([self.bases(ab) for ab in self.stats]) / len(self.stats)
```

## Team Class
The `Team` class represents a baseball team comprising multiple players.

### Initialization
```python
class Team:
    def __init__(self, players):
        self.players = players # List of Player instances
        self.record = [0, 0] # Initial 0-0 record, updated after each game
        ```
players: A list of Player instances.
record: A list to track wins and losses.

### update_record Method
Updates the team's win-loss record.

```python
def update_record(self, win):
    if win:
        self.record[0] += 1
    else:
        self.record[1] += 1
```

## Game Class
The `Game` class simulates a baseball game between two teams.

### Initialization
```python
class Game:
    def __init__(self, teams):
        self.teams = teams
        self.inning = 1
        self.outs = 0
        self.away_or_home = 0
        self.bases = [0, 0, 0]
        self.score = [0, 0]
        self.game_on = True
        self.current_player = [0, 0]
```
teams: A list of two Team instances.
inning, outs, bases, score, game_on, current_player: Variables to manage the state of the game.

### walker Method
Handles the scenario when a player walks.

```python
def walker(self):
    self.bases.append(0)
    self.bases[0] += 1
    for i in range(3):
        if self.bases[i] == 2:
            self.bases[i] -= 1
            self.bases[i + 1] += 1
    runs = self.bases[-1]
    self.bases = self.bases[:3]
    self.score[self.away_or_home] += runs
```

### hitter Method
Handles the scenario when a player hits.

```python
def hitter(self, hit_type):
    if hit_type == '1B':
        self.bases = [1, 0] + self.bases
    elif hit_type == '2B':
        self.bases = [0, 1] + self.bases
    elif hit_type == '3B':
        self.bases = [0, 0, 1] + self.bases
    elif hit_type == 'HR':
        self.bases = [0, 0, 0, 1] + self.bases
    runs = sum(self.bases[3:])
    self.bases = self.bases[:3]
    self.score[self.away_or_home] += runs
```

### handle_at_bat Method
Processes each at-bat, updating outs, score, and base runners.

```python
def handle_at_bat(self):
    player = self.teams[self.away_or_home].players[self.current_player[self.away_or_home]]
    result = player.at_bat()
    if result == 'OUT':
        self.outs += 1
    elif result == 'BB':
        self.walker()
    else:
        self.hitter(result)
    if (self.inning >= 9 and ((self.outs >= 3 and self.away_or_home == 0) or self.away_or_home == 1) and self.score[0] < self.score[1]) or (self.inning >= 9 and self.outs >= 3 and self.score[0] > self.score[1]):
        self.game_on = False
    if self.outs >= 3:
        if self.away_or_home == 1:
            self.inning += 1
        self.outs = 0
        self.current_player[self.away_or_home] = (self.current_player[self.away_or_home] + 1) % 9
        self.away_or_home = (self.away_or_home + 1) % 2
        self.bases = [0, 0, 0]
```

### play_game Method
Runs the game until completion, returns the final score and winner, and updates team records.

```python
def play_game(self):
    while self.game_on:
        self.handle_at_bat()
    final_score = copy.copy(self.score)
    winner = 1 if (self.score[0] < self.score[1]) else 0
    self.teams[0].record[winner] += 1
    self.teams[1].record[(winner + 1) % 2] += 1
    self.reset_game()
    return {
        "final_score": final_score,
        "winner": winner
    }

def reset_game(self):
    self.inning = 1
    self.outs = 0
    self.away_or_home = 0
    self.bases = [0, 0, 0]
    self.score = [0, 0]
    self.game_on = True
```

## Simulator Class
The `Simulator` class manages running multiple games and logging results.

### Initialization
```python
class Simulator:
    def __init__(self, teams):
        self.teams = teams
```

### simulate Method
Runs a specified number of games and logs the results.

```python
def simulate(self, its=100):
    game_log = []
    wins = 0
    for i in range(its):
        game = Game(self.teams)
        result = game.play_game()
        wins += result['winner']
        game_log.append(result)
    print(f"The home team won {wins} out of {its}, for a winning percentage of {wins / its * 100}%!")
    return game_log
```

## Example Usage
Here's how to use the script to simulate 100 games:

```python
# Define player probabilities
player_probs = {
    '1B': 0.2,
    '2B': 0.1,
    '3B': 0.05,
    'HR': 0.1,
    'WALK': 0.15,
    'OUT': 0.4
}

# Create players
players = [Player(player_probs) for _ in range(9)]

# Create two teams
team1 = Team(players)
team2 = Team(players)

# Initialize the simulator with two teams
simulator = Simulator([team1, team2])

# Run the simulation for 100 games
simulation_results = simulator.simulate(its=100)
```
This script allows you to simulate a series of baseball games, track individual player statistics, and team performance over multiple games. Whether you're a baseball enthusiast or a programmer interested in simulations, this project offers a fascinating way to explore the intricacies of the sport through code.

## Web UI

A lightweight browser UI is included so you can run simulations without touching Python code.

How to run

1. (Recommended) Create and activate a virtual environment and install dependencies:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start the web server:

```powershell
py -3 web_app.py
```

3. Open your browser at http://localhost:8000

What the UI does

- Lets you choose the number of games, random seed, and Dirichlet concentration (player variability).
- Optionally fetches team probabilities from Baseball-Reference (requires network + BeautifulSoup).
- Shows results in tidy tables and charts and offers a CSV download.

Troubleshooting

- If the web UI fails to start, check that Python is on your PATH and that dependencies are installed.
- If scraping fails due to SSL/proxy issues, run without "Use scrape" and the UI will use example probabilities.
