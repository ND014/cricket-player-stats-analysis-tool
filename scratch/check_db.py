import sqlite3

conn = sqlite3.connect('data/global_t20.db')
cursor = conn.cursor()
tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in tables:
    indices = [r[1] for r in cursor.execute(f"PRAGMA index_list({t})").fetchall()]
    print(f"Indices on {t}:", indices)
