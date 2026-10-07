import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('data/global_t20.db')

def test_head_to_head(p1, p2):
    # Check if p1 (batter) faced p2 (bowler)
    q = """
        SELECT 
            COUNT(*) as balls,
            SUM(runs_off_bat) as runs,
            SUM(CASE WHEN runs_off_bat = 0 THEN 1 ELSE 0 END) as dots,
            SUM(CASE WHEN runs_off_bat = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN runs_off_bat = 6 THEN 1 ELSE 0 END) as sixes,
            SUM(is_wicket) as dismissals
        FROM deliveries
        WHERE striker = ? AND bowler = ?
    """
    df = pd.read_sql(q, conn, params=(p1, p2))
    print(f"H2H: {p1} vs {p2}:")
    print(df)
    return df

test_head_to_head('V Kohli', 'Sandeep Sharma')
test_head_to_head('RG Sharma', 'SP Narine')
test_head_to_head('AD Russell', 'Rashid Khan')
