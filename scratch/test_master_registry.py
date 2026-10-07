import sqlite3
import pandas as pd
import rdata
import json
import re

# 1. Load data sources
conn = sqlite3.connect('data/global_t20.db')
db_strikers = pd.read_sql('SELECT striker as name, count(*) as balls FROM deliveries GROUP BY striker', conn)
db_bowlers = pd.read_sql('SELECT bowler as name, count(*) as balls FROM deliveries GROUP BY bowler', conn)
db_players = pd.concat([db_strikers, db_bowlers]).groupby('name')['balls'].sum().reset_index()
all_db_names = set(db_players['name'])
print(f"Total players in DB deliveries: {len(all_db_names)}")

# 2. Load Cricsheet people and names
df_people = pd.read_csv('data/cricsheet_people.csv')
df_names = pd.read_csv('data/cricsheet_names.csv')

# identifier -> cricsheet name and unique name
id_to_cric = dict(zip(df_people['identifier'], df_people['name']))
id_to_unique = dict(zip(df_people['identifier'], df_people['unique_name']))

# cric name -> identifier
cric_to_id = {}
for _, r in df_people.iterrows():
    cric_to_id[r['name']] = r['identifier']
    cric_to_id[r['unique_name']] = r['identifier']

# 3. Load names.csv variations (identifier -> list of names)
id_to_names_vars = {}
for _, r in df_names.iterrows():
    ident = r['identifier']
    name = str(r['name']).strip()
    id_to_names_vars.setdefault(ident, set()).add(name)

# 4. Load player_meta.rda (from cricketdata R package)
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

# 5. Familiar Name normalizer
# e.g. "David Andrew Miller" -> "David Miller"
# "Timothy Hays David" -> "Tim David"
# "Virat Kohli" -> "Virat Kohli"
# "Jasprit Jasbirsingh Bumrah" -> "Jasprit Bumrah"
# "Rohit Gurunath Sharma" -> "Rohit Sharma"
# "Kannaur Lokesh Rahul" -> "KL Rahul"

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
    'N Pooran': 'Nicholas Pooran',
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
    'Ashutosh Sharma': 'Ashutosh Sharma',
    'Shashank Singh': 'Shashank Singh'
}

# Helper to shorten formal 3-name strings like "David Andrew Miller" to "David Miller" if appropriate
def simplify_full_name(formal_name: str) -> str:
    if not formal_name or pd.isna(formal_name):
        return ""
    formal_name = str(formal_name).strip()
    parts = formal_name.split()
    if len(parts) == 3:
        # e.g. "David Andrew Miller" -> First + Last: "David Miller"
        # but check if middle is an initial like "A." or full
        return f"{parts[0]} {parts[2]}"
    elif len(parts) > 3:
        # e.g. "Abraham Benjamin de Villiers" -> "AB de Villiers" or "Abraham de Villiers"
        if "de Villiers" in formal_name:
            return "AB de Villiers"
        return f"{parts[0]} {parts[-1]}"
    return formal_name

# Now generate master registry for all 8325 players
registry = []
for p in sorted(list(all_db_names)):
    ident = cric_to_id.get(p)
    var_names = set(id_to_names_vars.get(ident, []))
    meta_full = id_to_meta_full.get(ident)
    meta_short = id_to_meta_short.get(ident)

    # 1. Best Full Name
    if p in KNOWN_PREFERRED_FULL_NAMES:
        full_name = KNOWN_PREFERRED_FULL_NAMES[p]
    elif meta_full:
        # Check if we have a simplified friendly version
        # e.g. "Timothy Hays David" -> "Tim David"
        # Check names.csv for friendly versions
        friendly_candidates = [v for v in var_names if len(v.split()) >= 2 and len(v) > len(p) and not any(len(w) == 1 for w in v.split())]
        if friendly_candidates:
            # pick shortest friendly candidate that has full first name
            full_name = sorted(friendly_candidates, key=lambda x: len(x))[0]
        else:
            full_name = simplify_full_name(meta_full)
    elif var_names:
        # Look in names.csv
        candidates = sorted(list(var_names), key=lambda x: (len(x.split()) > 1, len(x)), reverse=True)
        full_name = candidates[0]
    else:
        full_name = p

    # 2. Short name / initials
    # e.g. "DA Miller", "TH David", "V Kohli"
    cric_name = p

    # 3. Aliases list for sub-millisecond search
    # Includes:
    # - full_name (e.g. "David Miller", "david miller")
    # - cric_name (e.g. "DA Miller", "da miller")
    # - initials variants (e.g. "d miller", "d. miller", "miller")
    # - meta_full (e.g. "David Andrew Miller")
    # - all names.csv variations
    aliases = set()
    aliases.add(full_name.lower())
    aliases.add(cric_name.lower())
    if meta_full:
        aliases.add(meta_full.lower())
    if meta_short:
        aliases.add(meta_short.lower())
    for v in var_names:
        aliases.add(v.lower())

    # Add standard initials
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

    # Display string in UI:
    # If full_name is different from cric_name: "David Miller (DA Miller)"
    # If they are identical: "Abhishek Sharma"
    if full_name.lower() != cric_name.lower():
        display = f"{full_name} ({cric_name})"
    else:
        display = full_name

    registry.append({
        'cric_name': cric_name,
        'full_name': full_name,
        'display': display,
        'identifier': ident or '',
        'aliases': sorted(list(aliases))
    })

print(f"Generated registry for {len(registry)} players!")
# Test sample
test_keys = ['TH David', 'DA Miller', 'V Kohli', 'JJ Bumrah', 'RG Sharma', 'SA Yadav', 'KL Rahul', 'Abhishek Sharma', 'A Sharma', 'SC Ganguly', 'KA Pollard', 'M Theekshana']
for r in registry:
    if r['cric_name'] in test_keys:
        print(f"Cric: {r['cric_name']:<16} | Full: {r['full_name']:<20} | Display: {r['display']:<30} | Aliases sample: {r['aliases'][:5]}")
