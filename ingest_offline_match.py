"""
========================================================================================
OFFLINE MATCH INGESTOR — Global T20 Analytics Engine
========================================================================================
Processes newly played T20 match files completely OFFLINE without any WiFi or API calls.

HOW TO USE:
1. Transfer new match file(s) (Cricsheet CSV or JSON) into:
   data/incoming_matches/
2. Run this script:
   python ingest_offline_match.py
3. The matches are automatically parsed, enriched with archetypes, phases, and 
   legal ball metrics, and merged into 'data/global_t20.db'.
4. Processed files are safely archived in data/incoming_matches/processed/.
========================================================================================
"""

import os
import sys
import glob
import shutil
import sqlite3
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'global_t20.db')
INCOMING_DIR = os.path.join(DATA_DIR, 'incoming_matches')
PROCESSED_DIR = os.path.join(INCOMING_DIR, 'processed')

os.makedirs(INCOMING_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


def load_known_bowler_archetypes(conn):
    """Loads a mapping of known bowlers to their most frequent bowling archetype from DB."""
    q = """
        SELECT bowler, bowler_archetype, COUNT(*) as cnt
        FROM deliveries
        WHERE bowler_archetype IS NOT NULL AND bowler_archetype != 'UNKNOWN'
        GROUP BY bowler, bowler_archetype
        ORDER BY cnt DESC
    """
    df = pd.read_sql(q, conn)
    # Deduplicate to pick most frequent archetype per bowler
    df = df.drop_duplicates(subset=['bowler'])
    return dict(zip(df['bowler'], df['bowler_archetype']))


def get_tournament_code(name_str):
    """Maps tournament name or team names to standard tournament code."""
    if not name_str or pd.isna(name_str):
        return 'IPL'
    s = str(name_str).upper()
    if 'INDIAN PREMIER LEAGUE' in s or 'IPL' in s:
        return 'IPL'
    if 'BIG BASH' in s or 'BBL' in s:
        return 'BBL'
    if 'PAKISTAN SUPER LEAGUE' in s or 'PSL' in s:
        return 'PSL'
    if 'CARIBBEAN PREMIER LEAGUE' in s or 'CPL' in s:
        return 'CPL'
    if 'SUPER SMASH' in s:
        return 'SUPER_SMASH'
    if 'SYED MUSHTAQ' in s or 'SMAT' in s:
        return 'SMAT'
    if 'WORLD CUP' in s or 'ICC MEN\'S T20 WORLD CUP' in s:
        return 'T20_WORLD_CUP'
    if 'INTERNATIONAL' in s or 'T20I' in s:
        return 'T20I'
    if 'T20 BLAST' in s or 'VITALITY' in s or 'COUNTY' in s:
        return 'T20_BLAST'
    if 'SA20' in s:
        return 'SA20'
    if 'MAJOR LEAGUE' in s or 'MLC' in s:
        return 'MLC'
    if 'ILT20' in s or 'INTERNATIONAL LEAGUE' in s:
        return 'ILT20'
    if 'THE HUNDRED' in s:
        return 'THE_HUNDRED'
    if 'BPL' in s or 'BANGLADESH PREMIER' in s:
        return 'BPL'
    if 'LANKA PREMIER' in s or 'LPL' in s:
        return 'LPL'
    return 'OTHER_T20'


def get_league_tier(tournament_code):
    """Assigns tournament classification tier."""
    if tournament_code == 'IPL':
        return 'TIER_1_IPL'
    if tournament_code in ['T20I', 'T20_WORLD_CUP']:
        return 'INTERNATIONAL_T20'
    if tournament_code == 'SMAT':
        return 'DOMESTIC_SMAT'
    return 'GLOBAL_FRANCHISE'


def process_csv_match(filepath, conn, known_archetypes):
    """Parses a standard Cricsheet ball-by-ball CSV file."""
    df = pd.read_csv(filepath)
    if len(df) == 0:
        return 0, None

    # Check match_id
    match_id = int(df['match_id'].iloc[0])
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM deliveries WHERE match_id = ?", (match_id,))
    if cursor.fetchone()[0] > 0:
        print(f"[!] Match #{match_id} already exists in global_t20.db. Skipping duplicate.")
        return 0, match_id

    # Detect tournament
    season = str(df['season'].iloc[0]) if 'season' in df.columns else '2025'
    start_date = str(df['start_date'].iloc[0]) if 'start_date' in df.columns else ''
    venue = str(df['venue'].iloc[0]) if 'venue' in df.columns else ''
    
    # Check tournament column if available
    raw_tourn = df['tournament'].iloc[0] if 'tournament' in df.columns else 'IPL'
    tourn_code = get_tournament_code(raw_tourn)
    league_type = get_league_tier(tourn_code)

    # Derive over & phase
    df['over'] = df['ball'].astype(float).astype(int)
    df['phase'] = df['over'].apply(
        lambda o: 'Powerplay' if o < 6 else ('Middle' if o < 16 else 'Death')
    )

    # Bowler archetypes
    df['bowler_archetype'] = df['bowler'].map(known_archetypes).fillna('RAM')

    # Legal ball
    wides = df['wides'].fillna(0) if 'wides' in df.columns else 0
    df['is_legal_ball'] = (wides == 0).astype(int)

    # Extras
    noballs = df['noballs'].fillna(0) if 'noballs' in df.columns else 0
    byes = df['byes'].fillna(0) if 'byes' in df.columns else 0
    legbyes = df['legbyes'].fillna(0) if 'legbyes' in df.columns else 0
    extras = df['extras'].fillna(0) if 'extras' in df.columns else (wides + noballs + byes + legbyes)
    runs_bat = df['runs_off_bat'].fillna(0).astype(int)

    # Total runs conceded
    df['total_runs_conceded'] = (runs_bat + extras - byes - legbyes).astype(float)

    # Dots & boundaries
    df['is_dot'] = ((runs_bat == 0) & (extras == 0)).astype(int)
    df['is_boundary'] = runs_bat.isin([4, 6]).astype(int)

    # Wickets (excluding non-bowler wickets)
    w_type = df['wicket_type'].fillna('') if 'wicket_type' in df.columns else ''
    p_dism = df['player_dismissed'].fillna('') if 'player_dismissed' in df.columns else ''
    df['is_wicket'] = ((p_dism != '') & (~w_type.str.lower().isin(['run out', 'retired hurt', 'retired out', 'obstructing the field']))).astype(int)

    # Standard columns
    cols_to_insert = [
        'match_id', 'tournament', 'league_type', 'season', 'start_date', 'venue',
        'innings', 'ball', 'over', 'phase', 'batting_team', 'bowling_team',
        'striker', 'non_striker', 'bowler', 'bowler_archetype', 'runs_off_bat',
        'extras', 'wides', 'noballs', 'byes', 'legbyes', 'is_legal_ball',
        'is_dot', 'is_boundary', 'is_wicket', 'wicket_type', 'player_dismissed',
        'total_runs_conceded'
    ]

    df['tournament'] = tourn_code
    df['league_type'] = league_type

    # Ensure all columns exist
    for c in cols_to_insert:
        if c not in df.columns:
            df[c] = None

    insert_df = df[cols_to_insert]
    insert_df.to_sql('deliveries', conn, if_exists='append', index=False)
    conn.commit()

    return len(insert_df), match_id


def process_json_match(filepath, conn, known_archetypes):
    """Parses a standard Cricsheet JSON format match file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    info = data.get('info', {})
    match_id = info.get('match_type_number') or abs(hash(filepath)) % 10000000

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM deliveries WHERE match_id = ?", (match_id,))
    if cursor.fetchone()[0] > 0:
        print(f"[!] Match #{match_id} already exists in global_t20.db. Skipping duplicate.")
        return 0, match_id

    dates = info.get('dates', [''])
    start_date = dates[0] if dates else ''
    season = str(info.get('season', '2025'))
    venue = info.get('venue', '')
    event = info.get('event', {})
    tourn_name = event.get('name', 'IPL') if isinstance(event, dict) else str(event)
    tourn_code = get_tournament_code(tourn_name)
    league_type = get_league_tier(tourn_code)

    rows = []
    innings_list = data.get('innings', [])

    for inn_idx, inn in enumerate(innings_list, 1):
        team = inn.get('team', '')
        overs = inn.get('overs', [])
        # Find opponent team
        teams = info.get('teams', [])
        bowling_team = teams[1] if (len(teams) > 1 and teams[0] == team) else (teams[0] if len(teams) > 0 else '')

        for over_data in overs:
            over_num = int(over_data.get('over', 0))
            phase = 'Powerplay' if over_num < 6 else ('Middle' if over_num < 16 else 'Death')
            deliveries = over_data.get('deliveries', [])

            for b_idx, d in enumerate(deliveries, 1):
                ball_str = float(f"{over_num}.{b_idx}")
                batter = d.get('batter', '')
                non_striker = d.get('non_striker', '')
                bowler = d.get('bowler', '')
                arch = known_archetypes.get(bowler, 'RAM')

                runs_dict = d.get('runs', {})
                r_bat = int(runs_dict.get('batter', 0))
                r_extra = int(runs_dict.get('extras', 0))

                extras_dict = d.get('extras', {})
                wides = int(extras_dict.get('wides', 0))
                noballs = int(extras_dict.get('noballs', 0))
                byes = int(extras_dict.get('byes', 0))
                legbyes = int(extras_dict.get('legbyes', 0))

                is_legal = 1 if wides == 0 else 0
                is_dot = 1 if (r_bat == 0 and r_extra == 0) else 0
                is_boundary = 1 if r_bat in [4, 6] else 0
                runs_conceded = float(r_bat + r_extra - byes - legbyes)

                wickets = d.get('wickets', [])
                if wickets:
                    w0 = wickets[0]
                    w_kind = w0.get('kind', '')
                    p_out = w0.get('player_out', '')
                    is_wkt = 1 if w_kind.lower() not in ['run out', 'retired hurt', 'retired out'] else 0
                else:
                    w_kind = None
                    p_out = None
                    is_wkt = 0

                rows.append((
                    match_id, tourn_code, league_type, season, start_date, venue,
                    inn_idx, ball_str, over_num, phase, team, bowling_team,
                    batter, non_striker, bowler, arch, r_bat,
                    r_extra, (wides if wides > 0 else None), (noballs if noballs > 0 else None),
                    (byes if byes > 0 else None), (legbyes if legbyes > 0 else None),
                    is_legal, is_dot, is_boundary, is_wkt, w_kind, p_out, runs_conceded
                ))

    if not rows:
        return 0, match_id

    insert_sql = """
        INSERT INTO deliveries (
            match_id, tournament, league_type, season, start_date, venue,
            innings, ball, over, phase, batting_team, bowling_team,
            striker, non_striker, bowler, bowler_archetype, runs_off_bat,
            extras, wides, noballs, byes, legbyes, is_legal_ball,
            is_dot, is_boundary, is_wicket, wicket_type, player_dismissed,
            total_runs_conceded
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.executemany(insert_sql, rows)
    conn.commit()
    return len(rows), match_id


def run_ingestion():
    """Scans data/incoming_matches/ for new CSV/JSON match files and ingests them."""
    if not os.path.exists(DB_PATH):
        print(f"[!] Database not found at: {DB_PATH}")
        return

    csv_files = glob.glob(os.path.join(INCOMING_DIR, "*.csv"))
    json_files = glob.glob(os.path.join(INCOMING_DIR, "*.json"))
    all_files = csv_files + json_files

    if not all_files:
        print("=" * 80)
        print("[*] OFFLINE MATCH INGESTOR — IDLE")
        print("=" * 80)
        print(f"No match files found in: {INCOMING_DIR}")
        print("\nTo update with yesterday's match(es) offline:")
        print("1. Place the match .csv or .json file into:")
        print(f"   {INCOMING_DIR}")
        print("2. Re-run: python ingest_offline_match.py")
        print("=" * 80)
        return

    print("=" * 80)
    print(f"[*] Starting offline ingestion of {len(all_files)} match file(s)...")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    known_archetypes = load_known_bowler_archetypes(conn)

    total_deliveries = 0
    ingested_matches = 0

    for fpath in all_files:
        fname = os.path.basename(fpath)
        print(f"[*] Processing: {fname}...")
        try:
            if fpath.endswith('.csv'):
                count, mid = process_csv_match(fpath, conn, known_archetypes)
            else:
                count, mid = process_json_match(fpath, conn, known_archetypes)

            if count > 0:
                total_deliveries += count
                ingested_matches += 1
                print(f"    [+] Successfully added {count} deliveries for Match #{mid}!")
                # Move to processed
                shutil.move(fpath, os.path.join(PROCESSED_DIR, fname))
            else:
                # If duplicate or empty, move to processed to avoid re-checking
                shutil.move(fpath, os.path.join(PROCESSED_DIR, fname))

        except Exception as e:
            print(f"    [!] Error ingesting {fname}: {e}")

    conn.close()

    print("\n" + "=" * 80)
    print(f"[+] OFFLINE INGESTION COMPLETE!")
    print(f"    Matches added: {ingested_matches}")
    print(f"    Deliveries added: {total_deliveries:,}")
    print(f"    All player dossiers, wagon wheels, and matchup splits are now updated!")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    run_ingestion()
