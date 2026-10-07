import urllib.request
import zipfile
import io
import os
import sys
import sqlite3
import pandas as pd

sys.path.insert(0, os.getcwd())
import matchup_engine as me

new_leagues = {
    'CSA_T20': {
        'url': 'https://cricsheet.org/downloads/ctc_male_csv2.zip',
        'name': 'CSA T20 Challenge (South Africa Domestic)',
        'country': 'South Africa',
        'tier': 'Domestic'
    },
    'LPL': {
        'url': 'https://cricsheet.org/downloads/lpl_male_csv2.zip',
        'name': 'Lanka Premier League (Sri Lanka)',
        'country': 'Sri Lanka',
        'tier': 'Franchise'
    },
    'SL_CLUBS_T20': {
        'url': 'https://cricsheet.org/downloads/mct_male_csv2.zip',
        'name': 'Sri Lanka Major Clubs T20',
        'country': 'Sri Lanka',
        'tier': 'Domestic'
    },
    'MSL': {
        'url': 'https://cricsheet.org/downloads/msl_male_csv2.zip',
        'name': 'Mzansi Super League (South Africa)',
        'country': 'South Africa',
        'tier': 'Domestic'
    }
}

os.makedirs('data/leagues', exist_ok=True)
conn = sqlite3.connect('data/global_t20.db')

for code, info in new_leagues.items():
    print(f"\n[+] Processing {code} - {info['name']}...")
    csv_path = f"data/leagues/{code.lower()}.csv"
    try:
        if os.path.exists(csv_path):
            print(f"  Loading existing CSV: {csv_path}...")
            df = pd.read_csv(csv_path, low_memory=False)
        else:
            req = urllib.request.Request(info['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()
            
            zf = zipfile.ZipFile(io.BytesIO(content))
            csv_files = [f for f in zf.namelist() if f.endswith('.csv') and not f.endswith('_info.csv')]
            print(f"  Found {len(csv_files)} match CSVs in zip.")

            dfs = []
            for f in csv_files:
                try:
                    sub = pd.read_csv(zf.open(f), low_memory=False)
                    dfs.append(sub)
                except Exception:
                    pass

            df = pd.concat(dfs, ignore_index=True)
            df['tournament'] = code
            df['league_type'] = info['tier']
            if 'season' not in df.columns:
                df['season'] = 'Unknown'
            df.to_csv(csv_path, index=False)

        # Prepare for SQLite table
        # Compute required columns if missing
        if 'over' not in df.columns:
            df['over'] = df['ball'].astype(float).astype(int)
        if 'phase' not in df.columns:
            df['phase'] = df['over'].apply(lambda o: 'Powerplay' if o <= 5 else ('Middle' if o <= 14 else 'Death'))
        if 'is_legal_ball' not in df.columns:
            df['is_legal_ball'] = df['wides'].isna().astype(int)
        if 'is_dot' not in df.columns:
            df['is_dot'] = ((df['runs_off_bat'] == 0) & (df['wides'].isna()) & (df['noballs'].isna())).astype(int)
        if 'is_boundary' not in df.columns:
            df['is_boundary'] = df['runs_off_bat'].isin([4, 6]).astype(int)
        if 'is_wicket' not in df.columns:
            df['is_wicket'] = df['wicket_type'].notna().astype(int)
        if 'total_runs_conceded' not in df.columns:
            df['total_runs_conceded'] = df['runs_off_bat'].fillna(0) + df['wides'].fillna(0) + df['noballs'].fillna(0)
        if 'bowler_archetype' not in df.columns:
            df['bowler_archetype'] = df['bowler'].apply(me.classify_bowler)

        # Insert into database (deleting existing code rows if any)
        conn.execute("DELETE FROM deliveries WHERE tournament = ?", (code,))
        cols = [
            'match_id', 'tournament', 'league_type', 'season', 'start_date', 'venue',
            'innings', 'ball', 'over', 'phase', 'batting_team', 'bowling_team',
            'striker', 'non_striker', 'bowler', 'bowler_archetype', 'runs_off_bat',
            'extras', 'wides', 'noballs', 'byes', 'legbyes', 'is_legal_ball',
            'is_dot', 'is_boundary', 'is_wicket', 'wicket_type', 'player_dismissed',
            'total_runs_conceded'
        ]
        # Ensure all columns exist
        for c in cols:
            if c not in df.columns:
                df[c] = None

        df[cols].to_sql('deliveries', conn, if_exists='append', index=False)
        print(f"  Inserted {len(df):,} deliveries into data/global_t20.db for {code}!")

    except Exception as e:
        print(f"  Error processing {code}: {e}")

conn.commit()
print("\n[+] Verification:")
res = conn.execute("SELECT tournament, count(distinct match_id), count(*) FROM deliveries GROUP BY tournament ORDER BY count(*) DESC").fetchall()
for r in res:
    print(f"  {r[0]:<15} | Matches: {r[1]:<6} | Deliveries: {r[2]:,}")
total = conn.execute("SELECT count(distinct match_id), count(*), count(distinct striker), count(distinct bowler) FROM deliveries").fetchone()
print(f"\n[+] GRAND TOTAL: {total[0]:,} Matches | {total[1]:,} Deliveries | {total[2]:,} Batters | {total[3]:,} Bowlers across all major cricket countries!")
conn.close()
