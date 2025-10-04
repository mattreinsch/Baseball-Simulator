#!/usr/bin/env python3
"""Small WSGI web server to run the simulator and serve a minimal UI.

No external web framework required. Start with: py -3 web_app.py
Open http://localhost:8000 in your browser.
"""
import json
import pathlib
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs, urlparse

ROOT = pathlib.Path(__file__).parent

def read_index():
    p = ROOT / 'web_ui' / 'index.html'
    return p.read_text(encoding='utf-8')


def json_response(start_response, data, status='200 OK'):
    body = json.dumps(data).encode('utf-8')
    headers = [('Content-Type', 'application/json; charset=utf-8'), ('Content-Length', str(len(body)))]
    start_response(status, headers)
    return [body]


def text_response(start_response, text, status='200 OK'):
    body = text.encode('utf-8')
    headers = [('Content-Type', 'text/html; charset=utf-8'), ('Content-Length', str(len(body)))]
    start_response(status, headers)
    return [body]


def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    if path in ('/', '/index.html') and method == 'GET':
        return text_response(start_response, read_index())

    if path == '/simulate' and method == 'POST':
        try:
            size = int(environ.get('CONTENT_LENGTH') or 0)
        except Exception:
            size = 0
        body = environ['wsgi.input'].read(size) if size else b''
        try:
            payload = json.loads(body.decode('utf-8')) if body else {}
        except Exception as e:
            return json_response(start_response, {'error': 'invalid json', 'detail': str(e)}, status='400 Bad Request')

        # lazy-import simulator code
        try:
            from baseball_sim import Player, Team, Simulator
            from baseball_sim_tool import build_teams_from_template, build_teams_from_scrape
        except Exception as e:
            return json_response(start_response, {'error': 'import failed', 'detail': str(e)}, status='500 Internal Server Error')

        # parse parameters
        games = int(payload.get('games', 100))
        seed = payload.get('seed')
        concentration = float(payload.get('concentration', 50.0))
        use_scrape = bool(payload.get('use_scrape', False))
        year = int(payload.get('year', 2019))
        team1_name = payload.get('team1')
        team2_name = payload.get('team2')

        if seed is not None:
            import numpy as _np
            _np.random.seed(int(seed))

        try:
            if use_scrape:
                team1, team2 = build_teams_from_scrape(year, team1_name, team2_name, concentration=concentration)
            else:
                template_probs = {
                    '1B': 0.2,
                    '2B': 0.1,
                    '3B': 0.05,
                    'HR': 0.1,
                    'WALK': 0.15,
                    'OUT': 0.4
                }
                team1, team2 = build_teams_from_template(template_probs, seed=seed)

            sim = Simulator([team1, team2])
            game_log = sim.simulate_with_progress(its=games, show_progress=False)

            # produce summary
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

            team_summary, player_summary = summarize(sim)

            return json_response(start_response, {'team_summary': team_summary, 'players': player_summary, 'games': len(game_log)})
        except Exception as e:
            return json_response(start_response, {'error': 'simulation failed', 'detail': str(e)}, status='500 Internal Server Error')

    # serve static files from web_ui
    if path.startswith('/static/') or path.startswith('/web_ui/'):
        file_path = ROOT / path.lstrip('/')
        if file_path.exists() and file_path.is_file():
            return text_response(start_response, file_path.read_text(encoding='utf-8'))
        else:
            return text_response(start_response, 'Not found', status='404 Not Found')

    return text_response(start_response, read_index(), status='200 OK')


def run(port=8000):
    print(f"Starting web server on http://localhost:{port} ...")
    with make_server('', port, application) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('Shutting down')


if __name__ == '__main__':
    run()
