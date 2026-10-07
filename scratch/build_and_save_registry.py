import sqlite3
import pandas as pd
import rdata
import json
import os

print("[1/5] Connecting to SQLite database and gathering all unique players...")
conn = sqlite3.connect('data/global_t20.db')
db_strikers = pd.read_sql('SELECT striker as name, count(*) as balls FROM deliveries GROUP BY striker', conn)
db_bowlers = pd.read_sql('SELECT bowler as name, count(*) as balls FROM deliveries GROUP BY bowler', conn)
db_players = pd.concat([db_strikers, db_bowlers]).groupby('name')['balls'].sum().reset_index()
all_db_names = set(db_players['name'])
print(f"Total unique players in DB deliveries: {len(all_db_names)}")

print("[2/5] Loading Cricsheet register files...")
df_people = pd.read_csv('data/cricsheet_people.csv')
df_names = pd.read_csv('data/cricsheet_names.csv')

# identifier -> cricsheet match name and unique name
id_to_cric = dict(zip(df_people['identifier'], df_people['name']))
id_to_unique = dict(zip(df_people['identifier'], df_people['unique_name']))

# cric name -> identifier
cric_to_id = {}
for _, r in df_people.iterrows():
    cric_to_id[r['name']] = r['identifier']
    cric_to_id[r['unique_name']] = r['identifier']

# identifier -> set of names in names.csv
id_to_names_vars = {}
for _, r in df_names.iterrows():
    ident = r['identifier']
    name = str(r['name']).strip()
    id_to_names_vars.setdefault(ident, set()).add(name)

print("[3/5] Loading player_meta.rda for full expanded names...")
parsed = rdata.parser.parse_file('data/player_meta.rda')
converted = rdata.conversion.convert(parsed)
df_meta = list(converted.values())[0]

id_to_meta_full = {}
id_to_meta_short = {}
for _, r in df_meta.iterrows():
    cid = str(r['cricsheet_id']) if pd.notna(r['cricsheet_id']) else None
    if cid:
        if pd.notna(r['full_name']):
            id_to_meta_full[cid] = str(r['full_name']).strip()
        if pd.notna(r['name']):
            id_to_meta_short[cid] = str(r['name']).strip()

print(f"Loaded {len(id_to_meta_full)} full names from player_meta.rda")

# Curated high-profile friendly player names
KNOWN_PREFERRED_FULL_NAMES = {
    'V Kohli': 'Virat Kohli',
    'RG Sharma': 'Rohit Sharma',
    'JJ Bumrah': 'Jasprit Bumrah',
    'KL Rahul': 'KL Rahul',
    'SA Yadav': 'Suryakumar Yadav',
    'RR Pant': 'Rishabh Pant',
    'HH Pandya': 'Hardik Pandya',
    'MS Dhoni': 'MS Dhoni',
    'DA Miller': 'David Miller',
    'TH David': 'Tim David',
    'AB de Villiers': 'AB de Villiers',
    'KA Pollard': 'Kieron Pollard',
    'DJ Bravo': 'Dwayne Bravo',
    'CH Gayle': 'Chris Gayle',
    'F du Plessis': 'Faf du Plessis',
    'Q de Kock': 'Quinton de Kock',
    'AD Russell': 'Andre Russell',
    'SP Narine': 'Sunil Narine',
    'GJ Maxwell': 'Glenn Maxwell',
    'JC Buttler': 'Jos Buttler',
    'MA Starc': 'Mitchell Starc',
    'PJ Cummins': 'Pat Cummins',
    'TM Head': 'Travis Head',
    'H Klaasen': 'Heinrich Klaasen',
    'N Pooran': 'Nicholas Pooran',
    'MP Stoinis': 'Marcus Stoinis',
    'S Dube': 'Shivam Dube',
    'SS Iyer': 'Shreyas Iyer',
    'RM Patidar': 'Rajat Patidar',
    'NT Tilak Varma': 'Tilak Varma',
    'RK Singh': 'Rinku Singh',
    'AR Patel': 'Axar Patel',
    'RA Jadeja': 'Ravindra Jadeja',
    'YS Chahal': 'Yuzvendra Chahal',
    'R Bishnoi': 'Ravi Bishnoi',
    'CV Varun': 'Varun Chakravarthy',
    'T Natarajan': 'T Natarajan',
    'Harshal Patel': 'Harshal Patel',
    'Sandeep Sharma': 'Sandeep Sharma',
    'Mohammed Shami': 'Mohammed Shami',
    'Mohammed Siraj': 'Mohammed Siraj',
    'Arshdeep Singh': 'Arshdeep Singh',
    'Kuldeep Yadav': 'Kuldeep Yadav',
    'Rashid Khan': 'Rashid Khan',
    'Babar Azam': 'Babar Azam',
    'Shaheen Shah Afridi': 'Shaheen Shah Afridi',
    'Shubman Gill': 'Shubman Gill',
    'YBK Jaiswal': 'Yashasvi Jaiswal',
    'RD Gaikwad': 'Ruturaj Gaikwad',
    'SV Samson': 'Sanju Samson',
    'Abhishek Sharma': 'Abhishek Sharma',
    'B Sai Sudharsan': 'Sai Sudharsan',
    'Ishan Kishan': 'Ishan Kishan',
    'Riyan Parag': 'Riyan Parag',
    'KD Karthik': 'Dinesh Karthik',
    'R Tewatia': 'Rahul Tewatia',
    'Dhruv Jurel': 'Dhruv Jurel',
    'Ashutosh Sharma': 'Ashutosh Sharma',
    'M Shahrukh Khan': 'Shahrukh Khan',
    'Washington Sundar': 'Washington Sundar',
    'MA Agarwal': 'Mayank Agarwal',
    'A Nagwaswalla': 'Arzan Nagwaswalla',
    'A Sheth': 'Atit Sheth',
    'Akshay Karnewar': 'Akshay Karnewar',
    'KH Devdhar': 'Kedar Devdhar',
    'Vivek Singh': 'Vivek Singh',
    'Rohan Kadam': 'Rohan Kadam',
    'Priyank Panchal': 'Priyank Panchal',
    'Urvil Patel': 'Urvil Patel',
    'Cheepurapalli Stephen': 'Cheepurapalli Stephen',
    'Satyajeet Bachhav': 'Satyajeet Bachhav',
    'Tanmay Agarwal': 'Tanmay Agarwal',
    'Ashwin Hebbar': 'Ashwin Hebbar',
    'Suboth Bhati': 'Suboth Bhati',
    'Pankaj Jaswal': 'Pankaj Jaswal',
    'M Theekshana': 'Maheesh Theekshana',
    'TL Seifert': 'Tim Seifert',
    'R Shepherd': 'Romario Shepherd',
    'R Powell': 'Rovman Powell',
    'J Charles': 'Johnson Charles',
    'T Kohler-Cadmore': 'Tom Kohler-Cadmore',
    'LJ Evans': 'Laurie Evans',
    'LJ Wright': 'Luke Wright',
    'I Udana': 'Isuru Udana',
    'L Wood': 'Luke Wood',
    'RV Uthappa': 'Robin Uthappa',
    'A Mishra': 'Amit Mishra',
    'DA Payne': 'David Payne',
    'DJ Willey': 'David Willey',
    'JT Smuts': 'Jon-Jon Smuts',
    'CN Ackermann': 'Colin Ackermann',
    'Mahmudullah': 'Mahmudullah',
    'SC Ganguly': 'Sourav Ganguly',
    'BB McCullum': 'Brendon McCullum',
    'P Kumar': 'Praveen Kumar',
    'Z Khan': 'Zaheer Khan',
    'SR Tendulkar': 'Sachin Tendulkar',
    'V Sehwag': 'Virender Sehwag',
    'G Gambhir': 'Gautam Gambhir',
    'Yuvraj Singh': 'Yuvraj Singh',
    'SK Raina': 'Suresh Raina',
    'IK Pathan': 'Irfan Pathan',
    'YK Pathan': 'Yusuf Pathan',
    'Harbhajan Singh': 'Harbhajan Singh',
    'A Nehra': 'Ashish Nehra',
    'RP Singh': 'RP Singh',
    'MM Patel': 'Munaf Patel',
    'JH Kallis': 'Jacques Kallis',
    'DW Steyn': 'Dale Steyn',
    'M Morkel': 'Morne Morkel',
    'JA Morkel': 'Albie Morkel',
    'MEK Hussey': 'Michael Hussey',
    'DJ Hussey': 'David Hussey',
    'SR Watson': 'Shane Watson',
    'MG Johnson': 'Mitchell Johnson',
    'B Lee': 'Brett Lee',
    'SPD Smith': 'Steve Smith',
    'DA Warner': 'David Warner',
    'AJ Finch': 'Aaron Finch',
    'CA Lynn': 'Chris Lynn',
    'JM Bairstow': 'Jonny Bairstow',
    'BA Stokes': 'Ben Stokes',
    'JC Archer': 'Jofra Archer',
    'MM Ali': 'Moeen Ali',
    'SM Curran': 'Sam Curran',
    'TK Curran': 'Tom Curran',
    'LS Livingstone': 'Liam Livingstone',
    'PD Salt': 'Phil Salt',
    'HC Brook': 'Harry Brook',
    'W Hasaranga': 'Wanindu Hasaranga',
    'PVD Chameera': 'Dushmantha Chameera',
    'M Pathirana': 'Matheesha Pathirana',
    'SO Hetmyer': 'Shimron Hetmyer',
    'E Lewis': 'Evin Lewis',
    'BA King': 'Brandon King',
    'KR Mayers': 'Kyle Mayers',
    'AS Joseph': 'Alzarri Joseph',
    'O Thomas': 'Oshane Thomas',
    'Avesh Khan': 'Avesh Khan',
    'Mukesh Kumar': 'Mukesh Kumar',
    'Prasidh Krishna': 'Prasidh Krishna',
    'Umran Malik': 'Umran Malik',
    'Tushar Deshpande': 'Tushar Deshpande',
    'Vaibhav Arora': 'Vaibhav Arora',
    'Harshit Rana': 'Harshit Rana',
    'Mayank Yadav': 'Mayank Yadav',
    'Nitish Kumar Reddy': 'Nitish Kumar Reddy',
    'Sameer Rizvi': 'Sameer Rizvi',
    'Kumar Kushagra': 'Kumar Kushagra',
    'Angkrish Raghuvanshi': 'Angkrish Raghuvanshi',
    'Naman Dhir': 'Naman Dhir',
    'Shashank Singh': 'Shashank Singh'
}

NICKNAME_EXTRA_ALIASES = {
    'V Kohli': ['king kohli', 'chiku', 'cheeku', 'goat'],
    'RG Sharma': ['hitman', 'rohit'],
    'JJ Bumrah': ['boom boom', 'boom boom bumrah', 'jassi'],
    'MS Dhoni': ['thala', 'captain cool', 'msd', 'mahi'],
    'SA Yadav': ['sky', 'surya', 'mr 360'],
    'AB de Villiers': ['abd', 'mr 360', 'alien'],
    'GJ Maxwell': ['maxi', 'the big show'],
    'KL Rahul': ['kl', 'klr'],
    'RR Pant': ['spidey', 'pant'],
    'HH Pandya': ['kung fu pandya', 'hardik']
}

def simplify_full_name(formal_name: str) -> str:
    if not formal_name or pd.isna(formal_name):
        return ""
    formal_name = str(formal_name).strip()
    parts = formal_name.split()
    if len(parts) == 3:
        return f"{parts[0]} {parts[2]}"
    elif len(parts) > 3:
        if "de Villiers" in formal_name:
            return "AB de Villiers"
        return f"{parts[0]} {parts[-1]}"
    return formal_name

print("[4/5] Building master player registry records...")
registry_list = []
alias_to_cric_map = {}
cric_to_full_map = {}
full_to_cric_map = {}

balls_map = dict(zip(db_players['name'], db_players['balls']))

# Sort players by total deliveries descending so prominent players claim shared aliases first
sorted_db_names = sorted(list(all_db_names), key=lambda x: balls_map.get(x, 0), reverse=True)

for p in sorted_db_names:
    ident = cric_to_id.get(p)
    var_names = set(id_to_names_vars.get(ident, []))
    meta_full = id_to_meta_full.get(ident)
    meta_short = id_to_meta_short.get(ident)

    if p in KNOWN_PREFERRED_FULL_NAMES:
        full_name = KNOWN_PREFERRED_FULL_NAMES[p]
    elif meta_full:
        friendly_candidates = [v for v in var_names if len(v.split()) >= 2 and len(v) > len(p) and not any(len(w) == 1 for w in v.split())]
        if friendly_candidates:
            full_name = sorted(friendly_candidates, key=lambda x: len(x))[0]
        else:
            full_name = simplify_full_name(meta_full)
    elif var_names:
        candidates = sorted(list(var_names), key=lambda x: (len(x.split()) > 1, len(x)), reverse=True)
        full_name = candidates[0]
    else:
        full_name = p

    cric_name = p
    delivs = int(balls_map.get(p, 0))

    aliases = set()
    aliases.add(full_name.lower())
    aliases.add(cric_name.lower())
    if meta_full:
        aliases.add(meta_full.lower())
    if meta_short:
        aliases.add(meta_short.lower())
    for v in var_names:
        aliases.add(v.lower())

    # Standard initials
    full_parts = full_name.split()
    if len(full_parts) >= 2:
        first_init = full_parts[0][0].lower()
        last_name = full_parts[-1].lower()
        aliases.add(f"{first_init} {last_name}")
        aliases.add(f"{first_init}. {last_name}")
        aliases.add(f"{first_init}{last_name}")
        aliases.add(last_name)

    cric_parts = cric_name.split()
    if len(cric_parts) >= 2:
        first_c = cric_parts[0].lower()
        last_c = cric_parts[-1].lower()
        aliases.add(f"{first_c} {last_c}")
        if len(first_c) > 1:
            aliases.add(f"{first_c[0]} {last_c}")

    # Add nickname aliases
    if cric_name in NICKNAME_EXTRA_ALIASES:
        for n in NICKNAME_EXTRA_ALIASES[cric_name]:
            aliases.add(n.lower())

    # Clean display string
    if full_name.lower() != cric_name.lower():
        display = f"{full_name} ({cric_name})"
    else:
        display = full_name

    rec = {
        'cric_name': cric_name,
        'full_name': full_name,
        'display': display,
        'deliveries': delivs,
        'identifier': ident or '',
        'aliases': sorted(list(aliases))
    }
    registry_list.append(rec)

    cric_to_full_map[cric_name] = full_name
    full_to_cric_map[full_name.lower()] = cric_name
    for a in aliases:
        # Since sorted by deliveries desc, the higher-volume player claims the alias first!
        if a not in alias_to_cric_map:
            alias_to_cric_map[a] = cric_name
        elif a == full_name.lower() or a == cric_name.lower():
            # Exact match overrides
            alias_to_cric_map[a] = cric_name

print(f"Constructed {len(registry_list)} player records with {len(alias_to_cric_map)} alias mappings.")

print("[5/5] Saving player registry to SQLite DB and JSON cache...")
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS player_registry")
cur.execute("""
    CREATE TABLE player_registry (
        cric_name TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        display_name TEXT NOT NULL,
        identifier TEXT,
        deliveries INTEGER NOT NULL DEFAULT 0,
        aliases_json TEXT NOT NULL
    )
""")

for r in registry_list:
    cur.execute(
        "INSERT INTO player_registry (cric_name, full_name, display_name, identifier, deliveries, aliases_json) VALUES (?, ?, ?, ?, ?, ?)",
        (r['cric_name'], r['full_name'], r['display'], r['identifier'], r['deliveries'], json.dumps(r['aliases']))
    )

cur.execute("CREATE INDEX IF NOT EXISTS idx_registry_full ON player_registry (full_name)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_registry_display ON player_registry (display_name)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_registry_delivs ON player_registry (deliveries DESC)")
conn.commit()
conn.close()

# Save JSON cache
cache_path = 'data/player_registry.json'
with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump({
        'players': registry_list,
        'cric_to_full': cric_to_full_map,
        'alias_to_cric': alias_to_cric_map
    }, f, indent=2)

print(f"[+] Master player registry successfully built and saved to SQLite DB and {cache_path}!")
