import pandas as pd
import sqlite3

conn = sqlite3.connect('data/global_t20.db')
db_strikers = pd.read_sql('SELECT striker as name, count(*) as balls FROM deliveries GROUP BY striker', conn)
db_bowlers = pd.read_sql('SELECT bowler as name, count(*) as balls FROM deliveries GROUP BY bowler', conn)
db_players = pd.concat([db_strikers, db_bowlers]).groupby('name')['balls'].sum().reset_index().sort_values('balls', ascending=False)
print(f"Total players in DB: {len(db_players)}")

df_people = pd.read_csv('data/cricsheet_people.csv')
df_names = pd.read_csv('data/cricsheet_names.csv')

# identifier -> cricsheet name
id_to_cric = dict(zip(df_people['identifier'], df_people['name']))
# cric -> identifier
cric_to_id = dict(zip(df_people['name'], df_people['identifier']))

# Also handle unique_name
unique_to_id = dict(zip(df_people['unique_name'], df_people['identifier']))

# identifier -> set of names in names.csv
id_to_names = {}
for _, r in df_names.iterrows():
    id_to_names.setdefault(r['identifier'], set()).add(str(r['name']).strip())

# Check top 100 most active players in our DB
has_expansion = 0
no_expansion = []

for _, row in db_players.head(100).iterrows():
    p = row['name']
    ident = cric_to_id.get(p) or unique_to_id.get(p)
    vars_ = id_to_names.get(ident, set())
    # find any variation that looks like a full name (longer or has full first name)
    expansions = [v for v in vars_ if v != p and len(v.split()) >= len(p.split()) and len(v) > len(p)]
    if expansions:
        has_expansion += 1
    else:
        # Check if p is already a full name (first name > 2 letters)
        parts = p.split()
        if len(parts) >= 2 and len(parts[0]) > 2 and not parts[0].endswith('.'):
            # Already a full name!
            has_expansion += 1
        else:
            no_expansion.append((p, row['balls'], ident, vars_))

print(f"\nTop 100 players: {has_expansion} have full name or expansion, {len(no_expansion)} do not.")
print("\nTop players without expansion in names.csv:")
for item in no_expansion[:30]:
    print(item)
