import urllib.request
import json

def test():
    # 1. Test Index
    r = urllib.request.urlopen('http://127.0.0.1:5000/')
    print('GET / Status:', r.status)

    # 2. Test Search
    r_search = urllib.request.urlopen('http://127.0.0.1:5000/api/search?q=kohli')
    search_data = json.loads(r_search.read().decode('utf-8'))
    print('GET /api/search?q=kohli:', search_data)

    # 3. Test Census
    r_census = urllib.request.urlopen('http://127.0.0.1:5000/api/census')
    census_data = json.loads(r_census.read().decode('utf-8'))
    print(f"GET /api/census: Total Tournaments={len(census_data['census'])} | Total Matches={census_data['total_matches']:,}")

    # 4. Test Player Audit
    r_audit = urllib.request.urlopen('http://127.0.0.1:5000/api/player/audit?name=Virat%20Kohli')
    audit_data = json.loads(r_audit.read().decode('utf-8'))
    print(f"GET /api/player/audit: Player={audit_data['cric_name']} | Career Runs={audit_data['batting_stats']['total_runs']:,}")

    # 5. Test Wagon Wheel
    r_wagon = urllib.request.urlopen('http://127.0.0.1:5000/api/player/wagon?name=Virat%20Kohli&bowler_type=SLA')
    wagon_data = json.loads(r_wagon.read().decode('utf-8'))
    print(f"GET /api/player/wagon: Dominant={wagon_data['dominant_sector']['Sector']} ({wagon_data['dominant_sector']['Run_Pct']}%) | Image b64 length={len(wagon_data['image_b64'])}")

    # 6. Test Defensive Wheel
    r_def = urllib.request.urlopen('http://127.0.0.1:5000/api/player/defensive_wheel?name=Jasprit%20Bumrah&phase=Death')
    def_data = json.loads(r_def.read().decode('utf-8'))
    print(f"GET /api/player/defensive_wheel: Fortress={def_data['fortress_sector']['Sector']} | Image b64 length={len(def_data['image_b64'])}")

    # 7. Test Compare
    r_comp = urllib.request.urlopen('http://127.0.0.1:5000/api/compare?player1=Virat%20Kohli&player2=Sandeep%20Sharma')
    comp_data = json.loads(r_comp.read().decode('utf-8'))
    print(f"GET /api/compare: Type={comp_data['comparison_type']} | Has H2H={comp_data['has_h2h']} | Image b64 length={len(comp_data['image_b64'])}")

    print("\n[+] ALL ENDPOINTS RESPONDED WITH 200 OK AND VALID DATA!")

if __name__ == '__main__':
    test()
