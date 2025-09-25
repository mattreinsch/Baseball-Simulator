"""Helper to fetch team batting outcome probabilities from Baseball-Reference.

Provides get_team_prob_df(year) -> DataFrame with columns ['1B','2B','3B','HR','WALK','OUT'] and team names as index.
"""
import re
import requests
import pandas as pd
from html import unescape

try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except Exception:
    BeautifulSoup = None
    _HAS_BS4 = False


def get_team_prob_df(year: int, verify_ssl: bool = True) -> pd.DataFrame:
    """Fetch batting totals for MLB `year` and return normalized probabilities per team.

    Returns a DataFrame where each row is a team and columns are the six outcomes.
    """
    url = f"https://www.baseball-reference.com/leagues/MLB/{year}-standard-batting.shtml"
    resp = requests.get(url, verify=verify_ssl, timeout=15)
    resp.raise_for_status()

    html = resp.text

    if _HAS_BS4:
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        if table is None:
            raise RuntimeError('Could not find batting table on page')

        # header
        thead = table.find('thead')
        headers = [th.get_text(strip=True) for th in thead.find_all('th')]

        # rows
        rows = []
        for tr in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all('td')]
            if cells:
                rows.append(cells)
    else:
        # fallback naive parser: extract first <table>...</table> then parse thead and td cells with regex
        m = re.search(r"<table[^>]*>(.*?)</table>", html, flags=re.S | re.I)
        if not m:
            raise RuntimeError('Could not find table in HTML (no bs4 available)')
        table_html = m.group(1)

        # extract thead
        thead_match = re.search(r"<thead[^>]*>(.*?)</thead>", table_html, flags=re.S | re.I)
        if not thead_match:
            raise RuntimeError('Could not find thead in table (no bs4 available)')
        thead_html = thead_match.group(1)
        headers = [unescape(re.sub('<[^>]+>', '', th)).strip() for th in re.findall(r'<th[^>]*>(.*?)</th>', thead_html, flags=re.S | re.I)]

        # extract rows
        rows = []
        for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, flags=re.S | re.I):
            cells = [unescape(re.sub('<[^>]+>', '', td)).strip() for td in re.findall(r'<td[^>]*>(.*?)</td>', tr, flags=re.S | re.I)]
            if cells:
                rows.append(cells)

    if not rows:
        raise RuntimeError('No team rows parsed from table')

    stats = pd.DataFrame(rows, columns=headers[1:])

    # convert numeric cols where present
    numerical_cols = [c for c in ['PA', 'H', '2B', '3B', 'HR', 'BB', 'HBP', 'SF'] if c in stats.columns]
    for c in numerical_cols:
        stats[c] = pd.to_numeric(stats[c], errors='coerce').fillna(0)

    # compute singles, walks and outs
    # ensure columns exist
    stats['1B'] = stats.get('H', 0) - stats.get('2B', 0) - stats.get('3B', 0) - stats.get('HR', 0)
    stats['WALK'] = stats.get('BB', 0) + stats.get('HBP', 0)
    stats['OUT'] = stats.get('PA', 0) - (stats.get('H', 0) + stats['WALK'])

    df_probs = stats[['1B', '2B', '3B', 'HR', 'WALK', 'OUT']].copy()
    # some teams may have zeros; replace negative/zero sums with small epsilon to avoid division errors
    row_sums = df_probs.sum(axis=1).replace(0, 1)
    df_probs = df_probs.div(row_sums, axis=0)

    # try to determine team names from first cell in each original row (if available)
    # fallback: use DataFrame index
    first_col = headers[1] if len(headers) > 1 else None
    if first_col and first_col in stats.columns:
        df_probs.index = stats[first_col].astype(str)

    return df_probs
