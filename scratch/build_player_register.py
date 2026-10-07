import sqlite3
import pandas as pd
import urllib.request
import io
import os

db_path = 'data/global_t20.db'
conn = sqlite3.connect(db_path)
strikers = pd.read_sql("SELECT DISTINCT striker as name FROM deliveries", conn)['name'].tolist()
bowlers = pd.read_sql("SELECT DISTINCT bowler as name FROM deliveries", conn)['name'].tolist()
db_players = sorted(list(set(strikers + bowlers)))
print(f"Total unique players in global_t20.db: {len(db_players)}")

# Download or load people.csv and names.csv
people_path = 'data/cricsheet_people.csv'
names_path = 'data/cricsheet_names.csv'

if not os.path.exists(people_path):
    print("Downloading people.csv...")
    req = urllib.request.Request('https://cricsheet.org/register/people.csv', headers={'User-Agent': 'Mozilla/5.0'})
    with open(people_path, 'wb') as f:
        f.write(urllib.request.urlopen(req).read())

if not os.path.exists(names_path):
    print("Downloading names.csv...")
    req = urllib.request.Request('https://cricsheet.org/register/names.csv', headers={'User-Agent': 'Mozilla/5.0'})
    with open(names_path, 'wb') as f:
        f.write(urllib.request.urlopen(req).read())

df_people = pd.read_csv(people_path)
df_names = pd.read_csv(names_path)

print(f"people.csv: {len(df_people)} rows, names.csv: {len(df_names)} rows")

# Let's inspect how people and names map to db_players
# In people.csv: 'name' is the cricsheet match name (e.g. 'TH David', 'V Kohli', 'DA Miller')
# In names.csv: 'name' has full name variations (e.g. 'Tim David', 'Virat Kohli', 'David Miller')
people_map = {} # identifier -> cricsheet match name
for _, row in df_people.iterrows():
    people_map[row['identifier']] = row['name']

cric_to_full = {}
cric_to_variations = {}

for _, row in df_names.iterrows():
    ident = row['identifier']
    var_name = str(row['name']).strip()
    if ident in people_map:
        cric_name = people_map[ident]
        if cric_name not in cric_to_variations:
            cric_to_variations[cric_name] = set()
        cric_to_variations[cric_name].add(var_name)

# Pick the best full name for each cric_name
for cric_name, vars_set in cric_to_variations.items():
    # Candidates longer than cric_name, or containing spaces
    sorted_vars = sorted(list(vars_set), key=lambda x: (len(x.split()) > 1, len(x)), reverse=True)
    cric_to_full[cric_name] = sorted_vars[0]

matched = [p for p in db_players if p in cric_to_full]
print(f"Matched directly: {len(matched)} / {len(db_players)} players in DB have full names from Cricsheet register!")

# Let's check some popular names:
test_sample = ['TH David', 'DA Miller', 'V Kohli', 'JJ Bumrah', 'RG Sharma', 'SA Yadav', 'RR Pant', 'KL Rahul', 'MS Dhoni', 'GJ Maxwell', 'JC Buttler', 'Rashid Khan', 'AD Russell', 'Abhishek Sharma', 'A Sharma']
for t in test_sample:
    print(f"Cricsheet: '{t}' -> Full: '{cric_to_full.get(t, 'NOT FOUND')}' | All variations: {cric_to_variations.get(t, [])}")
