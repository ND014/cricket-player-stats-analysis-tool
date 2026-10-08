import sqlite3
import time

conn = sqlite3.connect('data/global_t20.db')
cursor = conn.cursor()

print("Building match_baselines table...")
t0 = time.time()

cursor.execute("DROP TABLE IF EXISTS match_baselines")
cursor.execute("""
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
    )
""")

# Populate match baselines with full phase granularity
cursor.execute("""
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
    GROUP BY match_id
""")

conn.commit()
t1 = time.time()
print(f"[+] match_baselines table built in {t1-t0:.2f}s!")

# Create index on match_id in deliveries if not exists
cursor.execute("CREATE INDEX IF NOT EXISTS idx_deliv_match ON deliveries(match_id)")
conn.commit()

# Test query speed for Virat Kohli
t2 = time.time()
cursor.execute("""
    SELECT 
        d.match_id,
        d.phase,
        d.runs_off_bat,
        mb.pitch_category,
        mb.match_rpb,
        CASE 
            WHEN d.phase = 'Powerplay' THEN mb.pp_rpb
            WHEN d.phase = 'Middle' THEN mb.mid_rpb
            WHEN d.phase = 'Death' THEN mb.dth_rpb
            ELSE mb.match_rpb
        END as expected_rpb
    FROM deliveries d
    JOIN match_baselines mb ON d.match_id = mb.match_id
    WHERE d.striker = 'V Kohli'
""")
rows = cursor.fetchall()
t3 = time.time()
print(f"[+] Queried {len(rows)} deliveries for V Kohli in {t3-t2:.4f}s (sub-second!)")

# Summary breakdown
import pandas as pd
df_test = pd.DataFrame(rows, columns=['match_id', 'phase', 'runs_off_bat', 'pitch_cat', 'match_rpb', 'exp_rpb'])
actual_runs = df_test['runs_off_bat'].sum()
expected_runs = df_test['exp_rpb'].sum()
run_value = actual_runs - expected_runs
print(f"Virat Kohli Career:")
print(f"  Actual Runs: {actual_runs}")
print(f"  Expected Runs (xR): {expected_runs:.1f}")
print(f"  Run Value (Runs Above Expected): {run_value:+.1f}")
print(f"  Contextual SR: {actual_runs / len(df_test) * 100:.1f} vs Expected SR: {expected_runs / len(df_test) * 100:.1f}")
print(f"  xR Impact: {actual_runs / expected_runs:.2f}x")

print("\nBy Pitch Difficulty:")
for pcat in ['HARD', 'BALANCED', 'EASY']:
    sub = df_test[df_test['pitch_cat'] == pcat]
    if len(sub) > 0:
        a_r = sub['runs_off_bat'].sum()
        e_r = sub['exp_rpb'].sum()
        rv = a_r - e_r
        sr = a_r / len(sub) * 100
        xsr = e_r / len(sub) * 100
        print(f"  [{pcat}] Balls: {len(sub)} | Actual: {a_r} | xR: {e_r:.1f} | RV: {rv:+.1f} | SR: {sr:.1f} vs xSR: {xsr:.1f} | Impact: {a_r/e_r:.2f}x")
