import sqlite3
import time

conn = sqlite3.connect('data/global_t20.db')
t0 = time.time()
cur = conn.cursor()
# Build an in-memory index or check speed of player table
res = cur.execute("""
    SELECT DISTINCT striker FROM deliveries WHERE striker LIKE 'V Kohl%'
""").fetchall()
print(f"Direct query ({time.time()-t0:.3f}s): {res}")

# Check distinct players count
t0 = time.time()
strikers = [r[0] for r in cur.execute("SELECT DISTINCT striker FROM deliveries").fetchall()]
bowlers = [r[0] for r in cur.execute("SELECT DISTINCT bowler FROM deliveries").fetchall()]
all_players = sorted(list(set(strikers + bowlers)))
print(f"Loaded {len(all_players)} distinct players in {time.time()-t0:.3f}s")
