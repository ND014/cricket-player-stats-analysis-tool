import sqlite3
import pandas as pd
import time

conn = sqlite3.connect('data/global_t20.db')

# Check match count and distribution
t0 = time.time()
df = pd.read_sql("""
    SELECT 
        match_id,
        venue,
        tournament,
        COUNT(*) as total_balls,
        SUM(runs_off_bat + extras) as total_runs,
        ROUND(1.0 * SUM(runs_off_bat + extras) / (COUNT(*) / 6.0), 2) as match_rpo
    FROM deliveries
    GROUP BY match_id
""", conn)
t1 = time.time()
print(f"Aggregated {len(df)} matches in {t1-t0:.2f}s")
print(df.describe())
print(df.head(10))
