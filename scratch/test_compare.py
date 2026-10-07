import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matchup_engine import resolve_player_name, auto_detect_player_meta, get_batter_phase_stats, get_bowler_phase_stats, get_batter_kryptonite

conn = sqlite3.connect('data/global_t20.db')

def prototype_compare(p1_name, p2_name, tournament='ALL'):
    c1 = resolve_player_name(p1_name)
    c2 = resolve_player_name(p2_name)
    
    # Load deliveries
    df1 = pd.read_sql("SELECT * FROM deliveries WHERE striker = ? OR bowler = ?", conn, params=(c1, c1))
    df2 = pd.read_sql("SELECT * FROM deliveries WHERE striker = ? OR bowler = ?", conn, params=(c2, c2))
    
    m1 = auto_detect_player_meta(c1, df1)
    m2 = auto_detect_player_meta(c2, df2)
    
    print(f"P1: {c1} ({m1['role']} - {m1['position']}) vs P2: {c2} ({m2['role']} - {m2['position']})")
    
    # Check H2H duel if batter vs bowler or both have deliveries
    q_h2h = """
        SELECT 
            COUNT(*) as balls,
            SUM(runs_off_bat) as runs,
            SUM(CASE WHEN runs_off_bat = 0 THEN 1 ELSE 0 END) as dots,
            SUM(CASE WHEN runs_off_bat = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN runs_off_bat = 6 THEN 1 ELSE 0 END) as sixes,
            SUM(is_wicket) as dismissals
        FROM deliveries 
        WHERE (striker = ? AND bowler = ?) OR (striker = ? AND bowler = ?)
    """
    df_h2h = pd.read_sql(q_h2h, conn, params=(c1, c2, c2, c1))
    print(f"H2H Records:\n{df_h2h}")
    
prototype_compare("Virat Kohli", "Rohit Sharma")
prototype_compare("Jasprit Bumrah", "Rashid Khan")
prototype_compare("Virat Kohli", "Sandeep Sharma")
