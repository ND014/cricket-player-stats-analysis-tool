import sqlite3
import pandas as pd

conn = sqlite3.connect('data/global_t20.db')
c = conn.cursor()

c.execute('SELECT COUNT(DISTINCT venue) FROM match_baselines WHERE venue IS NOT NULL AND length(venue) > 0')
total_venues = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM match_baselines')
total_matches = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM deliveries')
total_deliv = c.fetchone()[0]

c.execute('SELECT DISTINCT tournament FROM match_baselines')
tourns = [r[0] for r in c.fetchall()]

print(f"Total Unique Stadiums/Venues: {total_venues}")
print(f"Total Matches: {total_matches}")
print(f"Total Deliveries: {total_deliv}")
print(f"Total Tournaments/Leagues: {len(tourns)}")
print(f"Tournaments: {', '.join(tourns)}")

df = pd.read_sql("""
    SELECT venue, COUNT(*) as match_count, SUM(total_balls) as total_balls, AVG(par_score_20) as avg_par
    FROM match_baselines
    WHERE venue IS NOT NULL AND length(venue) > 0
    GROUP BY venue
    ORDER BY match_count DESC
""", conn)

print("\n--- TOP 30 STADIUMS WORLDWIDE BY MATCH VOLUME ---")
for idx, r in df.head(30).iterrows():
    print(f"  {idx+1:2d}. {r['venue']}: {r['match_count']} matches")

regions = {
    'India': ['Eden Gardens', 'Chinnaswamy', 'Wankhede', 'Feroz Shah', 'Arun Jaitley', 'Ahmedabad', 'Narendra Modi', 'MA Chidambaram', 'Chepauk', 'Rajiv Gandhi', 'Uppal', 'PCA', 'Mohali', 'Sawai Mansingh', 'BRSABV Ekana', 'Holkar', 'Green Park', 'JSCA', 'Barabati', 'Dr. Y.S. Rajasekhara'],
    'Australia': ['Melbourne Cricket Ground', 'Sydney Cricket Ground', 'Adelaide Oval', 'Brisbane Cricket Ground', 'Gabba', 'Perth Stadium', 'W.A.C.A', 'Bellerive Oval', 'Hobart', 'Manuka Oval', 'Simonds Stadium', 'Metricon'],
    'England & Wales': ["Lord's", 'The Oval', 'Edgbaston', 'Old Trafford', 'Trent Bridge', 'Headingley', 'Sophia Gardens', 'Cardiff', 'Rose Bowl', 'Southampton', 'Bristol', 'County Ground'],
    'UAE & Oman': ['Dubai International Cricket Stadium', 'Sharjah Cricket Stadium', 'Sheikh Zayed Stadium', 'Abu Dhabi', 'Al Amerat Cricket Ground'],
    'West Indies & Caribbean': ['Kensington Oval', 'Providence Stadium', "Queen's Park Oval", 'Brian Lara Stadium', 'Daren Sammy National Cricket Stadium', 'Warner Park', 'Sabina Park', 'Sir Vivian Richards'],
    'South Africa': ['Wanderers Stadium', 'SuperSport Park', 'Centurion', 'Newlands', 'Kingsmead', "St George's Park", 'Boland Park', 'Mangaung Oval'],
    'New Zealand': ['Eden Park', 'Seddon Park', 'Hagley Oval', 'Basin Reserve', 'Sky Stadium', 'Wellington Regional', 'Bay Oval', 'University Oval'],
    'Pakistan': ['Gaddafi Stadium', 'National Stadium', 'Rawalpindi Cricket Stadium', 'Multan Cricket Stadium', 'Arbab Niaz'],
    'Sri Lanka': ['R.Premadasa Stadium', 'Pallekele International Cricket Stadium', 'Sinhalese Sports Club', 'Mahinda Rajapaksa', 'Rangiri Dambulla'],
    'Bangladesh': ['Shere Bangla National Stadium', 'Zahur Ahmed Chowdhury Stadium', 'Sylhet International Cricket Stadium'],
    'USA': ['Central Broward Regional Park', 'Grand Prairie Stadium', 'Church Street Park', 'Nassau County International Cricket Stadium']
}

print("\n--- REGIONAL BREAKDOWN OF INDEXED GROUNDS ---")
for region, terms in regions.items():
    pattern = '|'.join([t.replace("'", "\\'") for t in terms])
    matched = df[df['venue'].str.contains(pattern, case=False, na=False)]
    print(f"  • {region}: {len(matched)} venues, {matched['match_count'].sum()} total matches")
