import sqlite3
import pandas as pd
import re

conn = sqlite3.connect('data/global_t20.db')
venues = pd.read_sql('SELECT venue, COUNT(*) as c FROM match_baselines GROUP BY venue ORDER BY venue', conn)

def clean_v(v):
    v = v.lower()
    v = re.sub(r'[,.\-\(\)]', ' ', v)
    v = re.sub(r'\s+', ' ', v).strip()
    return v

# Group by normalized root name
patterns = [
    (r'.*chinnaswamy.*', 'M Chinnaswamy Stadium, Bengaluru'),
    (r'.*wankhede.*', 'Wankhede Stadium, Mumbai'),
    (r'.*eden gardens.*', 'Eden Gardens, Kolkata'),
    (r'.*(?:chidambaram|chepauk).*', 'MA Chidambaram Stadium (Chepauk), Chennai'),
    (r'.*(?:arun jaitley|feroz shah kotla).*', 'Arun Jaitley Stadium, Delhi'),
    (r'.*rajiv gandhi.*', 'Rajiv Gandhi International Stadium, Hyderabad'),
    (r'.*(?:bindra|mohali|punjab cricket association).*', 'PCA IS Bindra Stadium, Mohali'),
    (r'.*(?:narendra modi|motera|sardar patel).*', 'Narendra Modi Stadium, Ahmedabad'),
    (r'.*sawai mansingh.*', 'Sawai Mansingh Stadium, Jaipur'),
    (r'.*(?:ekana|atal bihari vajpayee).*', 'BRSABV Ekana Stadium, Lucknow'),
    (r'.*brabourne.*', 'Brabourne Stadium, Mumbai'),
    (r'.*d\.?y\.?\s*patil.*', 'Dr DY Patil Sports Academy, Mumbai'),
    (r'.*holkar.*', 'Holkar Cricket Stadium, Indore'),
    (r'.*(?:maharashtra cricket association|subrata roy).*', 'MCA International Stadium, Pune'),
    (r'.*(?:green park).*', 'Green Park, Kanpur'),
    (r'.*(?:barabati).*', 'Barabati Stadium, Cuttack'),
    (r'.*(?:himachal pradesh|dharamsala|dharamshala).*', 'HPCA Stadium, Dharamshala'),
    (r'.*(?:sheikh zayed|zayed cricket).*', 'Sheikh Zayed Stadium, Abu Dhabi'),
    (r'.*dubai international.*', 'Dubai International Cricket Stadium'),
    (r'.*sharjah cricket.*', 'Sharjah Cricket Stadium'),
    (r'.*melbourne cricket ground.*', 'Melbourne Cricket Ground'),
    (r'.*sydney cricket ground.*', 'Sydney Cricket Ground'),
    (r'.*adelaide oval.*', 'Adelaide Oval'),
    (r'.*(?:gabba|brisbane cricket ground).*', 'The Gabba, Brisbane'),
    (r'.*(?:perth stadium|optus stadium).*', 'Perth Stadium (Optus)'),
    (r'.*(?:bellerive oval|hobart).*', 'Bellerive Oval, Hobart'),
    (r'.*kennington oval.*', 'The Oval, London'),
    (r'.*edgbaston.*', 'Edgbaston, Birmingham'),
    (r'.*old trafford.*', 'Old Trafford, Manchester'),
    (r'.*trent bridge.*', 'Trent Bridge, Nottingham'),
    (r'.*headingley.*', 'Headingley, Leeds'),
    (r'.*sophia gardens.*', 'Sophia Gardens, Cardiff'),
    (r'.*(?:rose bowl|southampton).*', 'The Rose Bowl, Southampton'),
    (r'.*shere bangla.*', 'Shere Bangla National Stadium, Mirpur'),
    (r'.*r\.?\s*premadasa.*', 'R Premadasa Stadium, Colombo'),
    (r'.*gaddafi.*', 'Gaddafi Stadium, Lahore'),
    (r'.*national stadium.*karachi.*', 'National Stadium, Karachi'),
    (r'.*rawalpindi.*', 'Rawalpindi Cricket Stadium'),
    (r'.*kensington oval.*', 'Kensington Oval, Barbados'),
    (r'.*providence stadium.*', 'Providence Stadium, Guyana'),
    (r'.*daren sammy.*', 'Daren Sammy Cricket Ground, St Lucia'),
    (r'.*queen\'?s park oval.*', "Queen's Park Oval, Trinidad"),
    (r'.*brian lara.*', 'Brian Lara Cricket Academy, Trinidad'),
    (r'.*warner park.*', 'Warner Park, St Kitts'),
    (r'.*wanderers.*', 'Wanderers Stadium, Johannesburg'),
    (r'.*(?:supersport park|centurion).*', 'SuperSport Park, Centurion'),
    (r'.*kingsmead.*', 'Kingsmead, Durban'),
    (r'.*newlands.*', 'Newlands, Cape Town'),
    (r'.*st george\'?s park.*', "St George's Park, Gqeberha"),
    (r'.*eden park.*', 'Eden Park, Auckland'),
    (r'.*seddon park.*', 'Seddon Park, Hamilton'),
    (r'.*hagley oval.*', 'Hagley Oval, Christchurch')
]

matched_venues = {}
for pattern, canonical in patterns:
    m = venues[venues['venue'].str.contains(pattern, case=False, na=False)]
    if len(m) > 1:
        matched_venues[canonical] = list(zip(m['venue'], m['c']))

print(f"Found {len(matched_venues)} venue groups with duplicates/variants:")
for can, items in matched_venues.items():
    tot = sum(c for _, c in items)
    print(f"\n* {can} (Total matches: {tot}):")
    for v, c in items:
        print(f"    - \"{v}\": {c} matches")
