"""
========================================================================================
BUILD MASTER GLOBAL T20 DATABASE (18 Worldwide Leagues & Tournaments)
========================================================================================
Fetches and merges all 18 major international and domestic T20 competitions from Cricsheet:
- IPL, T20 World Cup, T20Is, SMAT, BBL, PSL, CPL, SA20, CSA T20, MSL, LPL,
  Sri Lanka Major Clubs, BPL, Super Smash, Vitality T20 Blast, The Hundred, MLC, ILT20.

Builds deliveries, match_baselines, and player_registry tables with full indexes.
========================================================================================
"""

import os
import sys
import time
import zipfile
import urllib.request
import sqlite3
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from matchup_engine import normalize_venue_name, classify_bowler, BOWLER_ARCHETYPES, VENUE_MAPPINGS

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
ZIPS_DIR = os.path.join(DATA_DIR, 'zips')
os.makedirs(ZIPS_DIR, exist_ok=True)

TARGET_DB = os.path.join(DATA_DIR, 'global_t20_new.db')
FINAL_DB = os.path.join(DATA_DIR, 'global_t20.db')

TOURNAMENTS = [
    {
        'code': 'IPL',
        'url': 'https://cricsheet.org/downloads/ipl_male_csv2.zip',
        'local_file': os.path.join(DATA_DIR, 'ipl_male_csv2.zip'),
        'name': 'Indian Premier League',
        'tier': 'TIER_1_IPL'
    },
    {
        'code': 'T20_WORLD_CUP',
        'url': 'https://cricsheet.org/downloads/icc_mens_t20_world_cup_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'icc_mens_t20_world_cup_male_csv2.zip'),
        'name': "ICC Men's T20 World Cup",
        'tier': 'INTERNATIONAL_T20'
    },
    {
        'code': 'T20I',
        'url': 'https://cricsheet.org/downloads/t20s_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 't20s_male_csv2.zip'),
        'name': "Men's T20 Internationals",
        'tier': 'INTERNATIONAL_T20'
    },
    {
        'code': 'SMAT',
        'url': 'https://cricsheet.org/downloads/sma_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'sma_male_csv2.zip'),
        'name': 'Syed Mushtaq Ali Trophy',
        'tier': 'DOMESTIC_SMAT'
    },
    {
        'code': 'BBL',
        'url': 'https://cricsheet.org/downloads/bbl_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'bbl_male_csv2.zip'),
        'name': 'Big Bash League',
        'tier': 'GLOBAL_FRANCHISE'
    },
    {
        'code': 'PSL',
        'url': 'https://cricsheet.org/downloads/psl_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'psl_male_csv2.zip'),
        'name': 'Pakistan Super League',
        'tier': 'GLOBAL_FRANCHISE'
    },
    {
        'code': 'CPL',
        'url': 'https://cricsheet.org/downloads/cpl_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'cpl_male_csv2.zip'),
        'name': 'Caribbean Premier League',
        'tier': 'GLOBAL_FRANCHISE'
    },
    {
        'code': 'SA20',
        'url': 'https://cricsheet.org/downloads/sat_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'sat_male_csv2.zip'),
        'name': 'SA20 League',
        'tier': 'GLOBAL_FRANCHISE'
    },
    {
        'code': 'CSA_T20',
        'url': 'https://cricsheet.org/downloads/ctc_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'ctc_male_csv2.zip'),
        'name': 'CSA T20 Challenge',
        'tier': 'DOMESTIC'
    },
    {
        'code': 'MSL',
        'url': 'https://cricsheet.org/downloads/msl_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'msl_male_csv2.zip'),
        'name': 'Mzansi Super League',
        'tier': 'GLOBAL_FRANCHISE'
    },
    {
        'code': 'LPL',
        'url': 'https://cricsheet.org/downloads/lpl_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'lpl_male_csv2.zip'),
        'name': 'Lanka Premier League',
        'tier': 'GLOBAL_FRANCHISE'
    },
    {
        'code': 'SL_CLUBS_T20',
        'url': 'https://cricsheet.org/downloads/mct_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'mct_male_csv2.zip'),
        'name': 'Sri Lanka Major Clubs T20',
        'tier': 'DOMESTIC'
    },
    {
        'code': 'BPL',
        'url': 'https://cricsheet.org/downloads/bpl_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'bpl_male_csv2.zip'),
        'name': 'Bangladesh Premier League',
        'tier': 'GLOBAL_FRANCHISE'
    },
    {
        'code': 'SUPER_SMASH',
        'url': 'https://cricsheet.org/downloads/ssm_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'ssm_male_csv2.zip'),
        'name': 'Super Smash',
        'tier': 'DOMESTIC'
    },
    {
        'code': 'T20_BLAST',
        'url': 'https://cricsheet.org/downloads/ntb_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'ntb_male_csv2.zip'),
        'name': 'Vitality T20 Blast',
        'tier': 'DOMESTIC'
    },
    {
        'code': 'THE_HUNDRED',
        'url': 'https://cricsheet.org/downloads/hnd_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'hnd_male_csv2.zip'),
        'name': 'The Hundred',
        'tier': 'GLOBAL_FRANCHISE'
    },
    {
        'code': 'MLC',
        'url': 'https://cricsheet.org/downloads/mlc_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'mlc_male_csv2.zip'),
        'name': 'Major League Cricket',
        'tier': 'GLOBAL_FRANCHISE'
    },
    {
        'code': 'ILT20',
        'url': 'https://cricsheet.org/downloads/ilt_male_csv2.zip',
        'local_file': os.path.join(ZIPS_DIR, 'ilt_male_csv2.zip'),
        'name': 'International League T20',
        'tier': 'GLOBAL_FRANCHISE'
    }
]

EXPECTED_COLS = [
    'match_id', 'tournament', 'league_type', 'season', 'start_date', 'venue',
    'innings', 'ball', 'over', 'phase', 'batting_team', 'bowling_team',
    'striker', 'non_striker', 'bowler', 'bowler_archetype', 'runs_off_bat',
    'extras', 'wides', 'noballs', 'byes', 'legbyes', 'is_legal_ball',
    'is_dot', 'is_boundary', 'is_wicket', 'wicket_type', 'player_dismissed',
    'total_runs_conceded'
]

NON_BOWLER_WICKETS = {
    'run out', 'retired hurt', 'retired out', 'obstructing the field', 'hit the ball twice'
}


def download_file_if_needed(url, local_path):
    """Downloads zip file if not already present locally."""
    if os.path.exists(local_path) and os.path.getsize(local_path) > 10000:
        return local_path
    print(f"  Downloading: {url} -> {os.path.basename(local_path)}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Global T20 Pipeline)'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    with open(local_path, 'wb') as f:
        f.write(data)
    print(f"  Downloaded {len(data)/(1024*1024):.2f} MB.")
    return local_path


def load_known_bowler_archetypes():
    """Builds cache of known bowler archetypes from existing DB & hardcoded mappings."""
    known = dict(BOWLER_ARCHETYPES)
    if os.path.exists(FINAL_DB):
        try:
            conn = sqlite3.connect(FINAL_DB)
            q = """
                SELECT bowler, bowler_archetype, COUNT(*) as cnt
                FROM deliveries
                WHERE bowler_archetype IS NOT NULL AND bowler_archetype != 'UNKNOWN'
                GROUP BY bowler, bowler_archetype
                ORDER BY cnt DESC
            """
            df = pd.read_sql(q, conn)
            df = df.drop_duplicates(subset=['bowler'])
            for _, r in df.iterrows():
                if r['bowler'] not in known:
                    known[r['bowler']] = r['bowler_archetype']
            conn.close()
        except Exception:
            pass
    return known


def process_tournament_df(df, tourn_code, league_type, bowler_map):
    """Transforms raw Cricsheet csv2 DataFrame into schema-conforming deliveries DataFrame."""
    # Ensure all required raw columns exist
    for col in ['runs_off_bat', 'extras', 'wides', 'noballs', 'byes', 'legbyes', 'wicket_type', 'player_dismissed']:
        if col not in df.columns:
            df[col] = np.nan

    # Over and phase
    df['over'] = df['ball'].astype(float).astype(int)
    # Fast vectorized phase mapping
    over_vals = df['over'].values
    phases = np.where(over_vals < 6, 'Powerplay', np.where(over_vals < 16, 'Middle', 'Death'))
    df['phase'] = phases

    # Numeric conversions
    wides = df['wides'].fillna(0).astype(float).values
    noballs = df['noballs'].fillna(0).astype(float).values
    byes = df['byes'].fillna(0).astype(float).values
    legbyes = df['legbyes'].fillna(0).astype(float).values
    extras = df['extras'].fillna(0).astype(int).values
    runs_bat = df['runs_off_bat'].fillna(0).astype(int).values

    df['is_legal_ball'] = (wides == 0).astype(int)
    df['is_dot'] = ((runs_bat == 0) & (extras == 0)).astype(int)
    df['is_boundary'] = np.isin(runs_bat, [4, 6]).astype(int)

    w_type_str = df['wicket_type'].fillna('').astype(str).str.lower().values
    p_dism_str = df['player_dismissed'].fillna('').astype(str).values
    is_non_bowler = np.isin(w_type_str, list(NON_BOWLER_WICKETS))
    df['is_wicket'] = ((p_dism_str != '') & (~is_non_bowler)).astype(int)

    df['total_runs_conceded'] = (runs_bat + extras - byes - legbyes).astype(float)

    # Venue normalization
    v_series = df['venue'].fillna('Unknown Venue').astype(str).str.strip()
    df['venue'] = v_series.map(lambda v: VENUE_MAPPINGS.get(v, v))

    # Bowler archetype
    unique_bowlers = df['bowler'].dropna().unique()
    for b in unique_bowlers:
        if b not in bowler_map:
            bowler_map[b] = classify_bowler(b)
    df['bowler_archetype'] = df['bowler'].map(bowler_map).fillna('RAM')

    df['tournament'] = tourn_code
    df['league_type'] = league_type

    # Format return
    return df[EXPECTED_COLS]


def main():
    t_start = time.time()
    print("=" * 80)
    print("GLOBAL T20 MASTER DATABASE INGESTION (18 Worldwide Leagues)")
    print(f"Target Database: {TARGET_DB}")
    print("=" * 80)

    # Remove existing partial new DB
    if os.path.exists(TARGET_DB):
        os.remove(TARGET_DB)

    conn = sqlite3.connect(TARGET_DB)
    # SQLite performance tunings for bulk insert
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA journal_mode = MEMORY;")
    conn.execute("PRAGMA cache_size = 100000;")

    # Create deliveries table
    conn.execute("""
        CREATE TABLE deliveries (
            match_id INTEGER,
            tournament TEXT,
            league_type TEXT,
            season TEXT,
            start_date TEXT,
            venue TEXT,
            innings INTEGER,
            ball REAL,
            over INTEGER,
            phase TEXT,
            batting_team TEXT,
            bowling_team TEXT,
            striker TEXT,
            non_striker TEXT,
            bowler TEXT,
            bowler_archetype TEXT,
            runs_off_bat INTEGER,
            extras INTEGER,
            wides REAL,
            noballs REAL,
            byes REAL,
            legbyes REAL,
            is_legal_ball INTEGER,
            is_dot INTEGER,
            is_boundary INTEGER,
            is_wicket INTEGER,
            wicket_type TEXT,
            player_dismissed TEXT,
            total_runs_conceded REAL
        );
    """)

    bowler_map = load_known_bowler_archetypes()
    seen_match_ids = set()
    total_deliveries = 0

    for idx, tourn in enumerate(TOURNAMENTS, start=1):
        code = tourn['code']
        url = tourn['url']
        local_zip = tourn['local_file']
        name = tourn['name']
        tier = tourn['tier']

        print(f"\n[{idx}/{len(TOURNAMENTS)}] Processing {name} ({code})...")
        t0 = time.time()

        try:
            download_file_if_needed(url, local_zip)
            zf = zipfile.ZipFile(local_zip)
            
            if 'all_matches.csv' not in zf.namelist():
                print(f"  [!] No all_matches.csv in {local_zip}, checking individual match CSVs...")
                csv_files = [f for f in zf.namelist() if f.endswith('.csv') and not f.endswith('_info.csv')]
                sub_dfs = [pd.read_csv(zf.open(f), low_memory=False) for f in csv_files]
                raw_df = pd.concat(sub_dfs, ignore_index=True) if sub_dfs else pd.DataFrame()
            else:
                raw_df = pd.read_csv(zf.open('all_matches.csv'), low_memory=False)

            if len(raw_df) == 0:
                print(f"  [!] Empty dataset for {code}.")
                continue

            # De-duplicate matches
            initial_matches = raw_df['match_id'].nunique()
            raw_df = raw_df[~raw_df['match_id'].isin(seen_match_ids)]
            new_matches = raw_df['match_id'].nunique()
            if new_matches < initial_matches:
                print(f"  Filtered out {initial_matches - new_matches} matches already ingested in previous competitions.")

            if len(raw_df) == 0:
                print(f"  All matches for {code} were already ingested.")
                continue

            # Process dataframe
            clean_df = process_tournament_df(raw_df, code, tier, bowler_map)
            clean_df.to_sql('deliveries', conn, if_exists='append', index=False)
            
            new_match_ids = set(clean_df['match_id'].unique())
            seen_match_ids.update(new_match_ids)
            total_deliveries += len(clean_df)

            print(f"  [+] Ingested {len(clean_df):,} balls across {len(new_match_ids):,} matches in {time.time()-t0:.2f}s (Running total: {total_deliveries:,} balls, {len(seen_match_ids):,} matches)")

        except Exception as e:
            print(f"  [!] Error processing {code}: {e}")

    conn.commit()
    print("\n" + "=" * 80)
    print(f"DELIVERY INGESTION COMPLETE: {total_deliveries:,} deliveries | {len(seen_match_ids):,} matches")
    print("=" * 80)

    # -------------------------------------------------------------
    # BUILD MATCH BASELINES TABLE
    # -------------------------------------------------------------
    print("\n[*] Building match_baselines table...")
    t_base = time.time()
    conn.execute("""
        CREATE TABLE match_baselines (
            match_id INTEGER PRIMARY KEY,
            tournament TEXT,
            venue TEXT,
            season TEXT,
            start_date TEXT,
            total_balls INTEGER,
            total_runs INTEGER,
            match_rpo REAL,
            match_rpb REAL,
            par_score_20 REAL,
            pitch_category TEXT,
            pp_balls INTEGER,
            pp_runs INTEGER,
            pp_rpb REAL,
            mid_balls INTEGER,
            mid_runs INTEGER,
            mid_rpb REAL,
            dth_balls INTEGER,
            dth_runs INTEGER,
            dth_rpb REAL
        );
    """)

    conn.execute("""
        INSERT INTO match_baselines
        SELECT 
            match_id,
            MAX(tournament) as tournament,
            MAX(venue) as venue,
            MAX(season) as season,
            MIN(start_date) as start_date,
            COUNT(*) as total_balls,
            SUM(runs_off_bat + extras) as total_runs,
            ROUND(1.0 * SUM(runs_off_bat + extras) / (COUNT(*) / 6.0), 2) as match_rpo,
            ROUND(1.0 * SUM(runs_off_bat + extras) / COUNT(*), 4) as match_rpb,
            ROUND(1.0 * SUM(runs_off_bat + extras) / (COUNT(*) / 6.0) * 20.0, 1) as par_score_20,
            CASE 
                WHEN (1.0 * SUM(runs_off_bat + extras) / (COUNT(*) / 6.0) * 20.0) < 155 THEN 'HARD'
                WHEN (1.0 * SUM(runs_off_bat + extras) / (COUNT(*) / 6.0) * 20.0) >= 185 THEN 'EASY'
                ELSE 'BALANCED'
            END as pitch_category,
            
            -- Powerplay metrics
            SUM(CASE WHEN phase = 'Powerplay' THEN 1 ELSE 0 END) as pp_balls,
            SUM(CASE WHEN phase = 'Powerplay' THEN runs_off_bat + extras ELSE 0 END) as pp_runs,
            ROUND(CASE WHEN SUM(CASE WHEN phase = 'Powerplay' THEN 1 ELSE 0 END) > 0 
                  THEN 1.0 * SUM(CASE WHEN phase = 'Powerplay' THEN runs_off_bat + extras ELSE 0 END) / SUM(CASE WHEN phase = 'Powerplay' THEN 1 ELSE 0 END)
                  ELSE 1.25 END, 4) as pp_rpb,
                  
            -- Middle metrics
            SUM(CASE WHEN phase = 'Middle' THEN 1 ELSE 0 END) as mid_balls,
            SUM(CASE WHEN phase = 'Middle' THEN runs_off_bat + extras ELSE 0 END) as mid_runs,
            ROUND(CASE WHEN SUM(CASE WHEN phase = 'Middle' THEN 1 ELSE 0 END) > 0 
                  THEN 1.0 * SUM(CASE WHEN phase = 'Middle' THEN runs_off_bat + extras ELSE 0 END) / SUM(CASE WHEN phase = 'Middle' THEN 1 ELSE 0 END)
                  ELSE 1.25 END, 4) as mid_rpb,
                  
            -- Death metrics
            SUM(CASE WHEN phase = 'Death' THEN 1 ELSE 0 END) as dth_balls,
            SUM(CASE WHEN phase = 'Death' THEN runs_off_bat + extras ELSE 0 END) as dth_runs,
            ROUND(CASE WHEN SUM(CASE WHEN phase = 'Death' THEN 1 ELSE 0 END) > 0 
                  THEN 1.0 * SUM(CASE WHEN phase = 'Death' THEN runs_off_bat + extras ELSE 0 END) / SUM(CASE WHEN phase = 'Death' THEN 1 ELSE 0 END)
                  ELSE 1.70 END, 4) as dth_rpb
        FROM deliveries
        GROUP BY match_id;
    """)
    conn.commit()
    print(f"  [+] match_baselines table built in {time.time()-t_base:.2f}s!")

    # -------------------------------------------------------------
    # BUILD / COPY PLAYER REGISTRY
    # -------------------------------------------------------------
    print("\n[*] Populating player_registry table...")
    t_reg = time.time()
    conn.execute("""
        CREATE TABLE player_registry (
            cric_name TEXT PRIMARY KEY,
            full_name TEXT,
            display_name TEXT,
            identifier TEXT,
            deliveries INTEGER,
            aliases_json TEXT
        );
    """)

    # Compute deliveries count per player across all global deliveries
    player_balls_df = pd.read_sql("""
        SELECT player, SUM(cnt) as deliveries FROM (
            SELECT striker as player, count(*) as cnt FROM deliveries GROUP BY striker
            UNION ALL
            SELECT bowler as player, count(*) as cnt FROM deliveries GROUP BY bowler
        ) GROUP BY player
    """, conn)
    player_balls_map = dict(zip(player_balls_df['player'], player_balls_df['deliveries']))
    print(f"  Found {len(player_balls_map):,} unique players across all 18 competitions.")

    # Copy existing registry mappings if present
    existing_players = set()
    if os.path.exists(FINAL_DB):
        try:
            old_conn = sqlite3.connect(FINAL_DB)
            old_reg_df = pd.read_sql("SELECT * FROM player_registry", old_conn)
            old_conn.close()

            # Update deliveries count with global numbers
            old_reg_df['deliveries'] = old_reg_df['cric_name'].map(player_balls_map).fillna(old_reg_df['deliveries']).astype(int)
            old_reg_df.to_sql('player_registry', conn, if_exists='append', index=False)
            existing_players = set(old_reg_df['cric_name'])
            print(f"  Copied and refreshed {len(old_reg_df):,} existing player profiles.")
        except Exception as e:
            print(f"  [!] Note on copying player registry: {e}")

    # Add any new players who were not in the old registry
    new_players_rows = []
    for p, b_count in player_balls_map.items():
        if p not in existing_players:
            new_players_rows.append({
                'cric_name': p,
                'full_name': p,
                'display_name': p,
                'identifier': p,
                'deliveries': int(b_count),
                'aliases_json': '[]'
            })
    if new_players_rows:
        new_reg_df = pd.DataFrame(new_players_rows)
        new_reg_df.to_sql('player_registry', conn, if_exists='append', index=False)
        print(f"  Inserted {len(new_players_rows):,} newly registered worldwide players.")

    conn.commit()
    print(f"  [+] player_registry ready in {time.time()-t_reg:.2f}s!")

    # -------------------------------------------------------------
    # BUILD INDEXES
    # -------------------------------------------------------------
    print("\n[*] Creating high-performance SQLite indexes...")
    t_idx = time.time()
    conn.execute("CREATE INDEX idx_deliv_striker ON deliveries (striker);")
    conn.execute("CREATE INDEX idx_deliv_bowler ON deliveries (bowler);")
    conn.execute("CREATE INDEX idx_deliv_match ON deliveries (match_id);")
    conn.execute("CREATE INDEX idx_deliv_tourn ON deliveries (tournament);")
    conn.execute("CREATE INDEX idx_deliv_venue ON deliveries (venue);")
    conn.execute("CREATE INDEX idx_base_match ON match_baselines (match_id);")
    conn.execute("CREATE INDEX idx_registry_full ON player_registry (full_name);")
    conn.execute("CREATE INDEX idx_registry_display ON player_registry (display_name);")
    conn.execute("CREATE INDEX idx_registry_delivs ON player_registry (deliveries DESC);")
    conn.commit()
    conn.close()
    print(f"  [+] All indexes built in {time.time()-t_idx:.2f}s!")

    # -------------------------------------------------------------
    # ATOMIC SWAP
    # -------------------------------------------------------------
    print("\n[*] Performing atomic database replacement...")
    backup_db = os.path.join(DATA_DIR, 'global_t20_backup.db')
    if os.path.exists(FINAL_DB):
        if os.path.exists(backup_db):
            os.remove(backup_db)
        os.rename(FINAL_DB, backup_db)
    os.rename(TARGET_DB, FINAL_DB)
    print(f"  [+] Successfully replaced {FINAL_DB} with the new worldwide master database!")

    # -------------------------------------------------------------
    # VERIFICATION REPORT
    # -------------------------------------------------------------
    verify_conn = sqlite3.connect(FINAL_DB)
    v_c = verify_conn.cursor()
    v_c.execute("SELECT COUNT(*), COUNT(DISTINCT match_id), COUNT(DISTINCT venue) FROM deliveries;")
    delivs, matches, venues = v_c.fetchone()
    v_c.execute("SELECT COUNT(*) FROM player_registry;")
    total_players = v_c.fetchone()[0]

    print("\n" + "=" * 80)
    print("WORLDWIDE DATABASE SUMMARY:")
    print(f"  • Total Deliveries: {delivs:,}")
    print(f"  • Total Matches:    {matches:,}")
    print(f"  • Total Stadiums:   {venues:,} venues around the world!")
    print(f"  • Total Players:    {total_players:,}")
    print("-" * 80)
    print("Tournament Breakdown:")
    t_breakdown = verify_conn.execute("""
        SELECT tournament, COUNT(DISTINCT match_id), COUNT(*), COUNT(DISTINCT venue)
        FROM deliveries
        GROUP BY tournament
        ORDER BY COUNT(*) DESC;
    """).fetchall()
    for row in t_breakdown:
        print(f"  {row[0]:<15} | Matches: {row[1]:<6} | Deliveries: {row[2]:<10,} | Venues: {row[3]}")
    verify_conn.close()

    print("=" * 80)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {time.time()-t_start:.1f}s!")
    print("=" * 80)


if __name__ == '__main__':
    main()
