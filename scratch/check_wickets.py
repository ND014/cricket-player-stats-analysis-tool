import sqlite3
import pandas as pd

conn = sqlite3.connect('data/global_t20.db')
cols = [r[1] for r in conn.execute("PRAGMA table_info(deliveries)").fetchall()]
print("Deliveries columns:", cols)

query = """
    SELECT is_wicket, wicket_type, player_dismissed, phase 
    FROM deliveries 
    WHERE bowler = 'DJ Bravo' AND is_wicket = 1
"""
df = pd.read_sql(query, conn)
print(f"Total wickets for DJ Bravo in DB: {len(df)}")
print("\nWicket types breakdown:")
print(df['wicket_type'].value_counts())

death_df = df[df['phase'] == 'Death']
print(f"\nDeath overs wickets: {len(death_df)}")
print(death_df['wicket_type'].value_counts())
print("\nSample death wickets:")
print(death_df.head(20))
