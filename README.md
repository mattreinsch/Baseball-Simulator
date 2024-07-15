# Baseball-Simulator

This baseball simulation script models the outcomes of baseball games using probability distributions for player performance. It involves classes for players, teams, games, and a simulator to run multiple games. Here's a step-by-step breakdown:

Player Class:

Initialization: Takes a dictionary of probabilities for different outcomes (single, double, etc.) and stores it.
at_bat Method: Simulates a single at-bat by randomly choosing an outcome based on the player's probability distribution and records the outcome.
OBP Method: Calculates On-Base Percentage, which is the ratio of times the player gets on base (not 'OUT') to total at-bats.
AVE Method: Calculates Batting Average, the ratio of hits (excluding walks and outs) to total at-bats (excluding walks).
bases Method: Returns the number of bases for a given hit type.
slugging Method: Calculates the slugging percentage, the average number of bases per at-bat, including walks as one base.
Team Class:

Initialization: Takes a list of Player instances and initializes a record to track wins and losses.
update_record Method: Updates the team's win-loss record.
Game Class:

Initialization: Sets up the game with two teams, inning, outs, base runners, score, and current player index.
walker Method: Handles the scenario when a player walks, updating bases and score accordingly.
hitter Method: Handles the scenario when a player hits, updating bases and score based on the hit type.
handle_at_bat Method: Processes each at-bat, updating outs, score, and base runners, and checks if the game should continue or end.
play_game Method: Runs the game until completion, returns the final score and winner, and updates team records.
Simulator Class:

Initialization: Sets up the simulation with two teams and initial game conditions.
simulate Method: Runs a specified number of games, logs results, and prints the winning percentage of the home team.
Example Usage:

Define player probabilities for different outcomes.
Create players using the defined probabilities.
Create two teams with the created players.
Initialize the simulator with the two teams.
Run the simulation for 100 games and print the results.
This script allows for simulating a series of baseball games, tracking individual player statistics, and team performance over multiple games.
