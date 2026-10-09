import sqlite3
import pandas as pd

VENUE_MAPPINGS = {
    # Chinnaswamy
    "M Chinnaswamy Stadium": "M Chinnaswamy Stadium, Bengaluru",
    "M Chinnaswamy Stadium, Bangalore": "M Chinnaswamy Stadium, Bengaluru",
    "M.Chinnaswamy Stadium": "M Chinnaswamy Stadium, Bengaluru",
    
    # Wankhede
    "Wankhede Stadium": "Wankhede Stadium, Mumbai",
    
    # Eden Gardens
    "Eden Gardens": "Eden Gardens, Kolkata",
    
    # MA Chidambaram / Chepauk
    "MA Chidambaram Stadium": "MA Chidambaram Stadium (Chepauk), Chennai",
    "MA Chidambaram Stadium, Chepauk": "MA Chidambaram Stadium (Chepauk), Chennai",
    "MA Chidambaram Stadium, Chepauk, Chennai": "MA Chidambaram Stadium (Chepauk), Chennai",
    
    # Arun Jaitley / Kotla
    "Arun Jaitley Stadium": "Arun Jaitley Stadium, Delhi",
    "Feroz Shah Kotla": "Arun Jaitley Stadium, Delhi",
    
    # Rajiv Gandhi / Uppal
    "Rajiv Gandhi International Stadium": "Rajiv Gandhi International Stadium, Hyderabad",
    "Rajiv Gandhi International Stadium, Uppal": "Rajiv Gandhi International Stadium, Hyderabad",
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad": "Rajiv Gandhi International Stadium, Hyderabad",
    
    # PCA IS Bindra / Mohali
    "Punjab Cricket Association Stadium, Mohali": "PCA IS Bindra Stadium, Mohali",
    "Punjab Cricket Association IS Bindra Stadium": "PCA IS Bindra Stadium, Mohali",
    "Punjab Cricket Association IS Bindra Stadium, Mohali": "PCA IS Bindra Stadium, Mohali",
    "Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh": "PCA IS Bindra Stadium, Mohali",
    
    # Narendra Modi / Motera
    "Narendra Modi Stadium": "Narendra Modi Stadium, Ahmedabad",
    "Narendra Modi Stadium Ground 'A', Motera": "Narendra Modi Stadium, Ahmedabad",
    "Sardar Patel Stadium, Motera": "Narendra Modi Stadium, Ahmedabad",
    
    # Ekana Lucknow
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium": "BRSABV Ekana Stadium, Lucknow",
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium B": "BRSABV Ekana Stadium, Lucknow",
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow": "BRSABV Ekana Stadium, Lucknow",
    
    # Sawai Mansingh Jaipur
    "Sawai Mansingh Stadium": "Sawai Mansingh Stadium, Jaipur",
    
    # Brabourne Mumbai
    "Brabourne Stadium": "Brabourne Stadium, Mumbai",
    
    # Dr DY Patil Mumbai
    "Dr DY Patil Sports Academy": "Dr DY Patil Sports Academy, Mumbai",
    
    # Holkar Indore
    "Holkar Stadium": "Holkar Cricket Stadium, Indore",
    "Holkar Cricket Stadium": "Holkar Cricket Stadium, Indore",
    
    # MCA Pune / Subrata Roy
    "Maharashtra Cricket Association Stadium": "MCA International Stadium, Pune",
    "Subrata Roy Sahara Stadium": "MCA International Stadium, Pune",
    "Maharashtra Cricket Association Stadium, Pune": "MCA International Stadium, Pune",
    
    # Barabati Cuttack
    "Barabati Stadium": "Barabati Stadium, Cuttack",
    
    # Green Park Kanpur
    "Green Park": "Green Park, Kanpur",
    
    # HPCA Dharamsala
    "Himachal Pradesh Cricket Association Stadium": "HPCA Stadium, Dharamshala",
    "Himachal Pradesh Cricket Association Stadium, Dharamsala": "HPCA Stadium, Dharamshala",
    
    # JSCA Ranchi
    "JSCA International Stadium Complex": "JSCA International Stadium Complex, Ranchi",
    
    # Saurashtra Rajkot
    "Saurashtra Cricket Association Stadium": "Saurashtra Cricket Association Stadium, Rajkot",
    
    # Raipur
    "Shaheed Veer Narayan Singh International Stadium": "Shaheed Veer Narayan Singh Stadium, Raipur",
    "Shaheed Veer Narayan Singh International Stadium, Raipur": "Shaheed Veer Narayan Singh Stadium, Raipur",
    
    # VCA Nagpur
    "Vidarbha Cricket Association Stadium, Jamtha": "VCA Stadium, Jamtha, Nagpur",
    "Vidarbha Cricket Association Stadium, Jamtha, Nagpur": "VCA Stadium, Jamtha, Nagpur",
    
    # Mullanpur
    "Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur": "Maharaja Yadavindra Singh Stadium, Mullanpur",
    "Maharaja Yadavindra Singh International Cricket Stadium, New Chandigarh": "Maharaja Yadavindra Singh Stadium, Mullanpur",
    
    # Sheikh Zayed Abu Dhabi
    "Sheikh Zayed Stadium": "Sheikh Zayed Stadium, Abu Dhabi",
    "Zayed Cricket Stadium, Abu Dhabi": "Sheikh Zayed Stadium, Abu Dhabi",
    
    # The Gabba Brisbane
    "Brisbane Cricket Ground": "The Gabba, Brisbane",
    "Brisbane Cricket Ground, Woolloongabba": "The Gabba, Brisbane",
    "Brisbane Cricket Ground, Woolloongabba, Brisbane": "The Gabba, Brisbane",
    
    # Bellerive Oval Hobart
    "Bellerive Oval": "Bellerive Oval, Hobart",
    
    # The Oval London
    "Kennington Oval": "The Oval, London",
    "Kennington Oval, London": "The Oval, London",
    
    # Lord's London
    "Lord's": "Lord's, London",
    
    # Edgbaston Birmingham
    "Edgbaston": "Edgbaston, Birmingham",
    
    # Old Trafford Manchester
    "Old Trafford": "Old Trafford, Manchester",
    
    # Trent Bridge Nottingham
    "Trent Bridge": "Trent Bridge, Nottingham",
    
    # Headingley Leeds
    "Headingley": "Headingley, Leeds",
    
    # Sophia Gardens Cardiff
    "Sophia Gardens": "Sophia Gardens, Cardiff",
    
    # The Rose Bowl Southampton
    "The Rose Bowl": "The Rose Bowl, Southampton",
    
    # Shere Bangla Mirpur
    "Shere Bangla National Stadium": "Shere Bangla National Stadium, Mirpur",
    
    # R Premadasa Colombo
    "R Premadasa Stadium": "R Premadasa Stadium, Colombo",
    "R.Premadasa Stadium, Khettarama": "R Premadasa Stadium, Colombo",
    
    # Gaddafi Lahore
    "Gaddafi Stadium": "Gaddafi Stadium, Lahore",
    
    # Kensington Oval Barbados
    "Kensington Oval": "Kensington Oval, Barbados",
    "Kensington Oval, Bridgetown": "Kensington Oval, Barbados",
    "Kensington Oval, Bridgetown, Barbados": "Kensington Oval, Barbados",
    
    # Providence Guyana
    "Providence Stadium": "Providence Stadium, Guyana",
    
    # Daren Sammy St Lucia
    "Daren Sammy National Cricket Stadium, Gros Islet": "Daren Sammy Cricket Ground, St Lucia",
    "Daren Sammy National Cricket Stadium, Gros Islet, St Lucia": "Daren Sammy Cricket Ground, St Lucia",
    
    # Queen's Park Oval Trinidad
    "Queen's Park Oval, Port of Spain": "Queen's Park Oval, Trinidad",
    "Queen's Park Oval, Port of Spain, Trinidad": "Queen's Park Oval, Trinidad",
    
    # Brian Lara Trinidad
    "Brian Lara Stadium, Tarouba": "Brian Lara Cricket Academy, Trinidad",
    "Brian Lara Stadium, Tarouba, Trinidad": "Brian Lara Cricket Academy, Trinidad",
    
    # Warner Park St Kitts
    "Warner Park, Basseterre": "Warner Park, St Kitts",
    "Warner Park, Basseterre, St Kitts": "Warner Park, St Kitts",
    
    # Wanderers Johannesburg (NOT Windhoek)
    "New Wanderers Stadium": "Wanderers Stadium, Johannesburg",
    "New Wanderers Stadium, Johannesburg": "Wanderers Stadium, Johannesburg",
    "The Wanderers Stadium": "Wanderers Stadium, Johannesburg",
    "The Wanderers Stadium, Johannesburg": "Wanderers Stadium, Johannesburg",
    "Wanderers": "Wanderers Stadium, Johannesburg",
    
    # SuperSport Park Centurion
    "SuperSport Park": "SuperSport Park, Centurion",
    
    # Kingsmead Durban
    "Kingsmead": "Kingsmead, Durban",
    
    # Newlands Cape Town
    "Newlands": "Newlands, Cape Town",
    
    # St George's Park Gqeberha
    "St George's Park": "St George's Park, Gqeberha",
    "St George's Park, Port Elizabeth": "St George's Park, Gqeberha",
    
    # Seddon Park Hamilton
    "Seddon Park": "Seddon Park, Hamilton",
    
    # Hagley Oval Christchurch
    "Hagley Oval": "Hagley Oval, Christchurch",
    
    # Bay Oval Mount Maunganui
    "Bay Oval": "Bay Oval, Mount Maunganui",
    
    # Eden Park Auckland (main)
    "Eden Park": "Eden Park, Auckland",
    "Eden Park Outer Oval": "Eden Park Outer Oval, Auckland",
    
    # Manuka Oval Canberra
    "Manuka Oval": "Manuka Oval, Canberra",
    
    # Diamond Oval Kimberley
    "De Beers Diamond Oval": "Diamond Oval, Kimberley",
    "De Beers Diamond Oval, Kimberley": "Diamond Oval, Kimberley",
    
    # Mangaung Oval Bloemfontein
    "Mangaung Oval": "Mangaung Oval, Bloemfontein",
    "OUTsurance Oval": "Mangaung Oval, Bloemfontein",
    
    # P Sara Colombo
    "P Sara Oval": "P Sara Oval, Colombo",
    
    # Saxton Oval Nelson
    "Saxton Oval": "Saxton Oval, Nelson",
    
    # University Oval Dunedin
    "University Oval": "University Oval, Dunedin",
    
    # National Cricket Stadium Grenada
    "National Cricket Stadium, St George's": "National Cricket Stadium, Grenada",
    "National Cricket Stadium, St George's, Grenada": "National Cricket Stadium, Grenada",
    
    # Sabina Park Jamaica
    "Sabina Park, Kingston": "Sabina Park, Kingston, Jamaica",
    
    # Sir Vivian Richards Stadium Antigua
    "Sir Vivian Richards Stadium, North Sound": "Sir Vivian Richards Stadium, North Sound, Antigua",
    
    # The Village Malahide Dublin
    "The Village, Malahide": "The Village, Malahide, Dublin",
    
    # Sky Stadium Wellington
    "Sky Stadium": "Sky Stadium, Wellington",
    
    # McLean Park Napier
    "McLean Park": "McLean Park, Napier",
    
    # Zahur Ahmed Chowdhury Stadium Chittagong
    "Zahur Ahmed Chowdhury Stadium, Chittagong": "Zahur Ahmed Chowdhury Stadium, Chattogram",
    "Zahur Ahmed Chowdhury Stadium": "Zahur Ahmed Chowdhury Stadium, Chattogram",
    
    # Sheikh Abu Naser Stadium Khulna
    "Sheikh Abu Naser Stadium": "Sheikh Abu Naser Stadium, Khulna",
    
    # Tribhuvan University Kirtipur
    "Tribhuvan University International Cricket Ground": "Tribhuvan University Ground, Kirtipur",
    "Tribhuvan University International Cricket Ground, Kirtipur": "Tribhuvan University Ground, Kirtipur"
}

def migrate():
    conn = sqlite3.connect('data/global_t20.db')
    cur = conn.cursor()
    print("Checking current venue stats...")
    cur.execute("SELECT COUNT(DISTINCT venue) FROM match_baselines")
    print(f"Distinct in match_baselines before: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(DISTINCT venue) FROM deliveries")
    print(f"Distinct in deliveries before: {cur.fetchone()[0]}")
    
    # Ensure index on deliveries(venue) for rapid update
    print("Creating index on deliveries(venue) if not exists...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_deliv_venue ON deliveries(venue)")
    conn.commit()
    
    print("Applying venue canonical mappings...")
    updated_mb = 0
    updated_deliv = 0
    for old_v, new_v in VENUE_MAPPINGS.items():
        if old_v == new_v:
            continue
        cur.execute("UPDATE match_baselines SET venue = ? WHERE venue = ?", (new_v, old_v))
        updated_mb += cur.rowcount
        cur.execute("UPDATE deliveries SET venue = ? WHERE venue = ?", (new_v, old_v))
        updated_deliv += cur.rowcount
    
    conn.commit()
    print(f"Updated {updated_mb} match_baselines rows.")
    print(f"Updated {updated_deliv} deliveries rows.")
    
    cur.execute("SELECT COUNT(DISTINCT venue) FROM match_baselines")
    print(f"Distinct in match_baselines after: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(DISTINCT venue) FROM deliveries")
    print(f"Distinct in deliveries after: {cur.fetchone()[0]}")
    
    # Check Chinnaswamy specifically
    cur.execute("SELECT venue, COUNT(*) FROM match_baselines WHERE venue LIKE '%Chinnaswamy%' GROUP BY venue")
    print("\nChinnaswamy baselines after merge:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} matches")
        
    cur.execute("SELECT venue, COUNT(*) FROM deliveries WHERE venue LIKE '%Chinnaswamy%' GROUP BY venue")
    print("Chinnaswamy deliveries after merge:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} balls")
        
    # Check Wankhede
    cur.execute("SELECT venue, COUNT(*) FROM match_baselines WHERE venue LIKE '%Wankhede%' GROUP BY venue")
    print("\nWankhede baselines after merge:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} matches")
        
    # Check Chepauk
    cur.execute("SELECT venue, COUNT(*) FROM match_baselines WHERE venue LIKE '%Chidambaram%' OR venue LIKE '%Chepauk%' GROUP BY venue")
    print("\nChepauk baselines after merge:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} matches")
        
    conn.close()
    print("\nMigration complete successfully!")

if __name__ == '__main__':
    migrate()
