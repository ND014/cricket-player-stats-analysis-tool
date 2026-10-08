"""
========================================================================================
DAILY MATCH SYNC PIPELINE — Global T20 Analytics Engine
========================================================================================
Automatically fetches recently played T20 matches from Cricsheet's daily feed
and merges newly played games directly into 'data/global_t20.db'.

Features:
- Daily Cron / On-Demand Sync: Fetches matches added in the last 1, 2, or 7 days.
- Smart T20 Filtering: Filters for T20 leagues (IPL, BBL, PSL, CPL, SMAT, T20I, etc.).
- Duplicate Prevention: Never inserts an already-ingested match.
- Enriched Delivery Derivations: Bowler archetypes, legal deliveries, dots, 
  boundaries, wickets, wides, no-balls, and phase categorization.
========================================================================================
"""

import os
import sys
import io
import re
import argparse
import sqlite3
import zipfile
import urllib.request
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'global_t20.db')


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
    df = df.drop_duplicates(subset=['bowler'])
    return dict(zip(df['bowler'], df['bowler_archetype']))


def get_tournament_code(event_name):
    """Maps event name to standard tournament code."""
    if not event_name or pd.isna(event_name):
        return 'T20I'
    s = str(event_name).upper()
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
    if 'WORLD CUP' in s:
        return 'T20_WORLD_CUP'
    if 'VITALITY' in s or 'T20 BLAST' in s:
        return 'T20_BLAST'
    if 'SA20' in s:
        return 'SA20'
    if 'MAJOR LEAGUE' in s or 'MLC' in s:
        return 'MLC'
    if 'ILT20' in s or 'INTERNATIONAL LEAGUE' in s:
        return 'ILT20'
    if 'THE HUNDRED' in s:
        return 'THE_HUNDRED'
    if 'BANGLADESH PREMIER' in s or 'BPL' in s:
        return 'BPL'
    if 'LANKA PREMIER' in s or 'LPL' in s:
        return 'LPL'
    if 'TOUR OF' in s or 'INTERNATIONAL' in s or 'TRI-NATION' in s or 'SERIES' in s or 'CUP' in s:
        return 'T20I'
    return 'OTHER_T20'


def get_league_tier(tournament_code):
    if tournament_code == 'IPL':
        return 'TIER_1_IPL'
    if tournament_code in ['T20I', 'T20_WORLD_CUP']:
        return 'INTERNATIONAL_T20'
    if tournament_code == 'SMAT':
        return 'DOMESTIC_SMAT'
    return 'GLOBAL_FRANCHISE'


def parse_info_file(content_str):
    """Extracts metadata from a Cricsheet _info.csv file."""
    meta = {
        'match_type': 'T20',
        'event': '',
        'season': '2025/26',
        'start_date': '',
        'venue': '',
        'teams': []
    }
    for line in content_str.splitlines():
        parts = [p.strip().strip('"') for p in line.split(',')]
        if len(parts) >= 3 and parts[0] == 'info':
            key = parts[1]
            val = parts[2]
            if key == 'match_type':
                meta['match_type'] = val
            elif key == 'event':
                meta['event'] = val
            elif key == 'season':
                meta['season'] = val
            elif key == 'date' and not meta['start_date']:
                meta['start_date'] = val
            elif key == 'venue':
                meta['venue'] = val
            elif key == 'team':
                meta['teams'].append(val)
    return meta


def ingest_match_csv(zf, match_id, match_meta, conn, known_archetypes):
    """Parses match delivery CSV from zip file and appends to deliveries table."""
    csv_name = f"{match_id}.csv"
    if csv_name not in zf.namelist():
        return 0

    csv_bytes = zf.read(csv_name)
    df = pd.read_csv(io.BytesIO(csv_bytes))
    if len(df) == 0:
        return 0

    tourn_code = get_tournament_code(match_meta['event'])
    league_type = get_league_tier(tourn_code)
    season = match_meta['season']
    start_date = match_meta['start_date']
    venue = match_meta['venue']

    # Derivations
    df['match_id'] = int(match_id)
    df['tournament'] = tourn_code
    df['league_type'] = league_type
    df['season'] = season
    df['start_date'] = start_date
    df['venue'] = venue

    df['over'] = df['ball'].astype(float).astype(int)
    df['phase'] = df['over'].apply(
        lambda o: 'Powerplay' if o < 6 else ('Middle' if o < 16 else 'Death')
    )

    df['bowler_archetype'] = df['bowler'].map(known_archetypes).fillna('RAM')

    wides = df['wides'].fillna(0) if 'wides' in df.columns else 0
    noballs = df['noballs'].fillna(0) if 'noballs' in df.columns else 0
    byes = df['byes'].fillna(0) if 'byes' in df.columns else 0
    legbyes = df['legbyes'].fillna(0) if 'legbyes' in df.columns else 0
    extras = df['extras'].fillna(0) if 'extras' in df.columns else (wides + noballs + byes + legbyes)
    runs_bat = df['runs_off_bat'].fillna(0).astype(int)

    df['is_legal_ball'] = (wides == 0).astype(int)
    df['total_runs_conceded'] = (runs_bat + extras - byes - legbyes).astype(float)
    df['is_dot'] = ((runs_bat == 0) & (extras == 0)).astype(int)
    df['is_boundary'] = runs_bat.isin([4, 6]).astype(int)

    w_type = df['wicket_type'].fillna('') if 'wicket_type' in df.columns else ''
    p_dism = df['player_dismissed'].fillna('') if 'player_dismissed' in df.columns else ''
    df['is_wicket'] = ((p_dism != '') & (~w_type.str.lower().isin(['run out', 'retired hurt', 'retired out', 'obstructing the field']))).astype(int)

    cols = [
        'match_id', 'tournament', 'league_type', 'season', 'start_date', 'venue',
        'innings', 'ball', 'over', 'phase', 'batting_team', 'bowling_team',
        'striker', 'non_striker', 'bowler', 'bowler_archetype', 'runs_off_bat',
        'extras', 'wides', 'noballs', 'byes', 'legbyes', 'is_legal_ball',
        'is_dot', 'is_boundary', 'is_wicket', 'wicket_type', 'player_dismissed',
        'total_runs_conceded'
    ]

    for c in cols:
        if c not in df.columns:
            df[c] = None

    insert_df = df[cols]
    insert_df.to_sql('deliveries', conn, if_exists='append', index=False)
    conn.commit()
    return len(insert_df)


def sync_recent_matches(days=2):
    """
    Downloads Cricsheet recently_added zip and merges new T20 matches into global_t20.db.
    days: 2, 7, or 30
    """
    valid_days = [2, 7, 30]
    if days not in valid_days:
        days = 2

    zip_url = f"https://cricsheet.org/downloads/recently_added_{days}_csv2.zip"
    print("=" * 80)
    print(f"[*] CRICSHEET AUTO-SYNC PIPELINE (Last {days} Days)")
    print(f"[*] Target Feed: {zip_url}")
    print("=" * 80)

    incoming_dir = os.path.join(DATA_DIR, 'incoming_matches')
    os.makedirs(incoming_dir, exist_ok=True)
    sync_log_path = os.path.join(BASE_DIR, 'sync_log.md')

    # -------------------------------------------------------------
    # CLOUD / GITHUB ACTIONS MODE: Local DB not present on runner
    # -------------------------------------------------------------
    if not os.path.exists(DB_PATH):
        print(f"[*] Cloud runner detected (no local global_t20.db).")
        print(f"[*] Packaging new T20 matches into: {incoming_dir}")

        try:
            req = urllib.request.Request(zip_url, headers={'User-Agent': 'Mozilla/5.0 (Global T20 Engine)'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                zip_bytes = resp.read()
        except Exception as e:
            print(f"[!] Network error: {e}")
            return {'status': 'error', 'message': str(e)}

        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        info_files = [f for f in zf.namelist() if f.endswith('_info.csv')]
        extracted_matches = []

        for info_file in info_files:
            match_id_str = info_file.replace('_info.csv', '')
            content = zf.read(info_file).decode('utf-8')
            meta = parse_info_file(content)
            if 'T20' not in meta['match_type'].upper():
                continue

            # Extract both {match_id}.csv and {match_id}_info.csv into incoming_matches/
            csv_name = f"{match_id_str}.csv"
            if csv_name in zf.namelist():
                out_csv = os.path.join(incoming_dir, csv_name)
                out_info = os.path.join(incoming_dir, info_file)
                with open(out_csv, 'wb') as f:
                    f.write(zf.read(csv_name))
                with open(out_info, 'wb') as f:
                    f.write(zf.read(info_file))
                event = meta['event'] or 'T20'
                teams = " vs ".join(meta['teams']) if meta['teams'] else "Match"
                extracted_matches.append(f"#{match_id_str}: {event} ({teams})")

        # Write sync log
        import datetime
        now_str = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        log_content = f"# Daily T20 Match Auto-Sync Log\n\n"
        log_content += f"**Last Run:** {now_str}\n\n"
        log_content += f"**Matches Captured:** {len(extracted_matches)}\n\n"
        for m in extracted_matches:
            log_content += f"- {m}\n"

        with open(sync_log_path, 'w', encoding='utf-8') as f:
            f.write(log_content)

        print(f"[+] Extracted {len(extracted_matches)} T20 match files into incoming_matches/ for commit!")
        return {'status': 'success', 'new_matches': len(extracted_matches), 'details': extracted_matches}

    # -------------------------------------------------------------
    # LOCAL ENGINE MODE: Directly ingest into data/global_t20.db
    # -------------------------------------------------------------
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # First ingest any matches waiting in data/incoming_matches/
    from ingest_offline_match import process_csv_match, load_known_bowler_archetypes as load_known_arch
    known_archetypes = load_known_arch(conn)
    waiting_csvs = [f for f in glob.glob(os.path.join(incoming_dir, "*.csv")) if not f.endswith('_info.csv')]
    for wf in waiting_csvs:
        try:
            cnt, mid = process_csv_match(wf, conn, known_archetypes)
            if cnt > 0:
                print(f"[+] Ingested waiting local match #{mid} ({cnt} balls)")
            proc_dir = os.path.join(incoming_dir, 'processed')
            os.makedirs(proc_dir, exist_ok=True)
            shutil.move(wf, os.path.join(proc_dir, os.path.basename(wf)))
        except Exception as e:
            pass

    # Get set of all existing match IDs
    cursor.execute("SELECT DISTINCT match_id FROM deliveries")
    existing_match_ids = set(r[0] for r in cursor.fetchall())
    print(f"[*] Local database currently contains {len(existing_match_ids):,} matches.")

    try:
        req = urllib.request.Request(zip_url, headers={'User-Agent': 'Mozilla/5.0 (Global T20 Engine)'})
        print(f"[*] Fetching latest match package from Cricsheet...")
        with urllib.request.urlopen(req, timeout=30) as resp:
            zip_bytes = resp.read()
        print(f"[+] Downloaded package ({len(zip_bytes) / 1024:.1f} KB). Parsing matches...")
    except Exception as e:
        print(f"[!] Network error fetching Cricsheet zip: {e}")
        conn.close()
        return {'status': 'error', 'message': f'Network error: {str(e)}'}

    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))

    # Locate all _info.csv files
    info_files = [f for f in zf.namelist() if f.endswith('_info.csv')]
    new_t20_matches = 0
    total_deliveries_added = 0
    added_details = []

    for info_file in info_files:
        match_id_str = info_file.replace('_info.csv', '')
        try:
            match_id = int(match_id_str)
        except ValueError:
            continue

        if match_id in existing_match_ids:
            continue

        # Parse match metadata
        content = zf.read(info_file).decode('utf-8')
        meta = parse_info_file(content)

        # Only process T20 matches (ignore Tests, ODIs, etc.)
        if 'T20' not in meta['match_type'].upper():
            continue

        deliv_count = ingest_match_csv(zf, match_id, meta, conn, known_archetypes)
        if deliv_count > 0:
            new_t20_matches += 1
            total_deliveries_added += deliv_count
            existing_match_ids.add(match_id)
            event_name = meta['event'] or meta['match_type']
            teams_str = " vs ".join(meta['teams']) if meta['teams'] else "Match"
            added_details.append(f"#{match_id} ({event_name} • {teams_str} • {deliv_count} balls)")
            print(f"    [+] Ingested #{match_id}: {event_name} ({teams_str}) — {deliv_count} deliveries")

    conn.close()

    # Update sync_log.md
    import datetime
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_content = f"# Local T20 Match Auto-Sync Log\n\n"
    log_content += f"**Last Run:** {now_str}\n\n"
    log_content += f"**New Matches Ingested:** {new_t20_matches}\n"
    log_content += f"**New Deliveries Ingested:** {total_deliveries_added:,}\n"
    log_content += f"**Total Matches in DB:** {len(existing_match_ids):,}\n\n"
    for d in added_details:
        log_content += f"- {d}\n"
    with open(sync_log_path, 'w', encoding='utf-8') as f:
        f.write(log_content)

    print("\n" + "=" * 80)
    if new_t20_matches > 0:
        print(f"[+] SYNC SUCCESSFUL!")
        print(f"    New T20 matches added: {new_t20_matches}")
        print(f"    New deliveries added:  {total_deliveries_added:,}")
        print(f"    Database total matches: {len(existing_match_ids):,}")
    else:
        print(f"[*] UP TO DATE: No new un-ingested T20 matches in the last {days} days.")
    print("=" * 80 + "\n")

    return {
        'status': 'success',
        'new_matches': new_t20_matches,
        'new_deliveries': total_deliveries_added,
        'details': added_details
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Daily Cricsheet Match Sync")
    parser.add_argument('--days', type=int, default=2, choices=[2, 7, 30], help="Days lookback window (default: 2)")
    args = parser.parse_args()
    sync_recent_matches(days=args.days)
