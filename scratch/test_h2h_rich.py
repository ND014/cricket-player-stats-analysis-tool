import sqlite3
import pandas as pd

conn = sqlite3.connect('data/global_t20.db')
c1, c2 = 'V Kohli', 'A Kamboj'

q = """
    SELECT 
        match_id, start_date, tournament, phase, over, ball,
        striker, bowler, runs_off_bat, total_runs_conceded,
        is_dot, is_boundary, is_wicket, wicket_type, player_dismissed
    FROM deliveries
    WHERE (striker = ? AND bowler = ?) OR (striker = ? AND bowler = ?)
    ORDER BY start_date, match_id, over, ball
"""
df = pd.read_sql(q, conn, params=(c1, c2, c2, c1))
print(f"Total Balls: {len(df)}")
print(df)

# Group by Phase
for ph, pdf in df.groupby('phase'):
    runs = pdf['runs_off_bat'].sum()
    balls = len(pdf)
    outs = pdf['is_wicket'].sum()
    sr = runs * 100 / max(1, balls)
    dots = pdf['is_dot'].sum()
    fours = (pdf['runs_off_bat'] == 4).sum()
    sixes = (pdf['runs_off_bat'] == 6).sum()
    print(f"\nPhase: {ph}")
    print(f"  Balls: {balls} | Runs: {runs} | SR: {sr:.1f} | Outs: {outs} | Dots: {dots} | 4s: {fours} | 6s: {sixes}")
