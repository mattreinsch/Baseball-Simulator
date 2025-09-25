#!/usr/bin/env python3
"""Baseball Simulator CLI

Usage examples:
  python baseball_sim_tool.py --games 100 --seed 42 --out results.csv
  python baseball_sim_tool.py --games 100 --no-scrape

This script wraps the simulator and provides options for reproducible runs and CSV output.
"""
import argparse
import csv
import random
import sys
from typing import List

try:
    # prefer local module
    from baseball_sim import Player, Team, Simulator
    from baseball_scrape import get_team_prob_df
except Exception:
    print("Error importing local simulator or scraper. Make sure this script is run from the repository root and dependencies are installed.")
    raise


def build_teams_from_template(template_probs, seed=None):
    """Create two teams by sampling player-level probabilities from a Dirichlet centered on template_probs."""
    import pandas as _pd
    return build_rosters_from_team_probs(_pd.Series(template_probs), concentration=50.0, seed=seed)


def build_rosters_from_team_probs(team_probs, concentration=50.0, n_players=9, seed=None):
    """Sample two rosters whose player probability vectors are drawn from a Dirichlet centered on `team_probs`.

    team_probs: pd.Series-like with indexed probabilities for the outcome labels.
    """
    import numpy as _np
    import pandas as _pd

    if seed is not None:
        _np.random.seed(seed)

    labels = list(team_probs.index)
    base = _np.array(team_probs.values, dtype=float)
    if base.sum() == 0:
        base = _np.ones_like(base)
    base = base / base.sum()

    def make_team():
        players = []
        for _ in range(n_players):
            a = base * float(concentration)
            sampled = _np.random.dirichlet(a)
            probs_series = _pd.Series(sampled, index=labels)
            players.append(Player(probs_series))
        return Team(players)

    return make_team(), make_team()


def build_teams_from_scrape(year: int, team1_name: str = None, team2_name: str = None, verify_ssl: bool = True, concentration: float = 50.0):
    df = get_team_prob_df(year, verify_ssl=verify_ssl)
    if df.empty:
        raise RuntimeError('No team probabilities returned from scraper')

    names = list(df.index)
    if team1_name is None:
        team1_name = names[0]
    if team2_name is None:
        # pick a different team
        team2_name = names[1] if len(names) > 1 else names[0]

    if team1_name not in df.index or team2_name not in df.index:
        raise ValueError(f"Requested teams not found. Available: {', '.join(names[:10])} ...")

    team1_probs = df.loc[team1_name]
    team2_probs = df.loc[team2_name]

    # sample player-level probabilities for each team using the provided concentration
    team1 = build_rosters_from_team_probs(team1_probs, concentration=concentration)[0]
    team2 = build_rosters_from_team_probs(team2_probs, concentration=concentration)[1]
    return team1, team2


def write_results_csv(path: str, game_log: List[dict]):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['game_index', 'winner', 'score_home', 'score_away'])
        for i, g in enumerate(game_log, 1):
            h, a = g['final_score']
            writer.writerow([i, g['winner'], h, a])


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run the Baseball Simulator')
    parser.add_argument('--games', '-g', type=int, default=100, help='Number of games to simulate')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility')
    parser.add_argument('--out', '-o', type=str, default=None, help='Write game log to CSV')
    parser.add_argument('--no-scrape', action='store_true', help='Do not attempt scraping; use example probabilities')
    parser.add_argument('--use-scrape', action='store_true', help='Fetch team probabilities from Baseball-Reference for a given year')
    parser.add_argument('--year', type=int, default=2019, help='Year to fetch from baseball-reference when using --use-scrape')
    parser.add_argument('--team1', type=str, default=None, help='Team name for team1 when scraping')
    parser.add_argument('--team2', type=str, default=None, help='Team name for team2 when scraping')
    parser.add_argument('--concentration', type=float, default=50.0, help='Dirichlet concentration parameter for sampling player-level variability (higher => less variance)')
    parser.add_argument('--no-progress', action='store_true', help='Disable progress output')
    parser.add_argument('--out-summary', type=str, default=None, help='Write per-player and team summary to CSV')
    args = parser.parse_args(argv)

    # example probability distribution used when not scraping
    template_probs = {
        '1B': 0.2,
        '2B': 0.1,
        '3B': 0.05,
        'HR': 0.1,
        'WALK': 0.15,
        'OUT': 0.4
    }

    if args.seed is not None:
        import numpy as _np
        _np.random.seed(args.seed)

    # build teams
    if args.use_scrape and not args.no_scrape:
        try:
            team1, team2 = build_teams_from_scrape(args.year, team1_name=args.team1, team2_name=args.team2, concentration=args.concentration)
        except Exception as e:
            print(f"Scrape failed: {e}. Falling back to example probabilities.")
            team1, team2 = build_teams_from_template(template_probs, concentration=args.concentration, seed=args.seed)
    else:
        team1, team2 = build_teams_from_template(template_probs, concentration=args.concentration, seed=args.seed)
    simulator = Simulator([team1, team2])

    print(f"Simulating {args.games} games...")
    game_log = simulator.simulate_with_progress(its=args.games, show_progress=(not args.no_progress))

    if args.out:
        write_results_csv(args.out, game_log)
        print(f"Wrote results to {args.out}")

    # Produce per-player and team summaries from simulator state
    def summarize(sim):
        teams = sim.teams
        team_summaries = []
        player_rows = []
        for t_idx, team in enumerate(teams):
            wins, losses = team.record
            team_summaries.append({'team': t_idx, 'wins': wins, 'losses': losses})
            for p_idx, player in enumerate(team.players):
                obp = player.OBP() if hasattr(player, 'OBP') else 0
                ave = player.AVE() if hasattr(player, 'AVE') else 0
                slg = player.slugging() if hasattr(player, 'slugging') else 0
                player_rows.append({'team': t_idx, 'player': p_idx, 'OBP': obp, 'AVE': ave, 'SLG': slg})
        return team_summaries, player_rows

    team_summary, player_summary = summarize(simulator)

    # print a compact summary
    # Pretty-print summaries
    try:
        from tabulate import tabulate
        use_tabulate = True
    except Exception:
        use_tabulate = False

    print('\nTeam summary:')
    if use_tabulate:
        print(tabulate([(t['team'], t['wins'], t['losses']) for t in team_summary], headers=['team','wins','losses']))
    else:
        for t in team_summary:
            print(f" Team {t['team']}: {t['wins']} - {t['losses']}")

    print('\nTop players by OBP:')
    top_players = sorted(player_summary, key=lambda r: r['OBP'], reverse=True)[:10]
    if use_tabulate:
        print(tabulate([(p['team'], p['player'], f"{p['OBP']:.3f}", f"{p['AVE']:.3f}", f"{p['SLG']:.3f}") for p in top_players], headers=['team','player','OBP','AVE','SLG']))
    else:
        for p in top_players:
            print(f" Team {p['team']} Player {p['player']}: OBP={p['OBP']:.3f} AVE={p['AVE']:.3f} SLG={p['SLG']:.3f}")

    if args.out_summary:
        import csv
        with open(args.out_summary, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['type','team','player','OBP','AVE','SLG','wins','losses'])
            writer.writeheader()
            for t in team_summary:
                writer.writerow({'type':'team','team':t['team'],'wins':t['wins'],'losses':t['losses']})
            for p in player_summary:
                writer.writerow({'type':'player','team':p['team'],'player':p['player'],'OBP':p['OBP'],'AVE':p['AVE'],'SLG':p['SLG']})
        print(f"Wrote summary to {args.out_summary}")


if __name__ == '__main__':
    main()
