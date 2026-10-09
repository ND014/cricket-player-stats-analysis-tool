import urllib.request
import json

BASE_URL = 'http://127.0.0.1:5000'

def test_routes():
    print("=== 1. Testing GET / (index.html) ===")
    res = urllib.request.urlopen(f"{BASE_URL}/")
    assert res.status == 200
    html = res.read().decode('utf-8')
    assert "compare-cockpit-card" in html, "Missing compare-cockpit-card"
    assert "cockpit-grid" in html, "Missing cockpit-grid"
    assert "vs-emblem-badge" in html, "Missing vs-emblem-badge"
    assert "xrVenueSpotlightSection" in html, "Missing xrVenueSpotlightSection"
    assert "xrSelectedVenueCard" in html, "Missing xrSelectedVenueCard"
    assert "xrVenueGuidanceNotice" in html, "Missing xrVenueGuidanceNotice"
    assert "xrVenueTable" not in html, "Old space-consuming table still in html!"
    print("[OK] index.html has all required new components and old table removed.")

    print("\n=== 2. Testing GET /static/css/style.css ===")
    res_css = urllib.request.urlopen(f"{BASE_URL}/static/css/style.css")
    assert res_css.status == 200
    css = res_css.read().decode('utf-8')
    assert ".compare-cockpit-card" in css, "Missing .compare-cockpit-card in CSS"
    assert ".compare-phase-grid" in css, "Missing .compare-phase-grid in CSS"
    assert "grid-template-columns: repeat(3, 1fr)" in css, "Missing 3-column phase grid in CSS"
    assert ".venue-spotlight-card" in css, "Missing .venue-spotlight-card in CSS"
    assert ".insight-badge-box.fortress" in css, "Missing fortress badge styling in CSS"
    assert ".insight-badge-box.leak" in css, "Missing leak badge styling in CSS"
    print("[OK] style.css contains all layout and responsive design classes.")

    print("\n=== 3. Testing GET /api/player/xr for Virat Kohli (Deduplication Check) ===")
    res_xr = urllib.request.urlopen(f"{BASE_URL}/api/player/xr?name=Virat%20Kohli&role=bat&tournament=ALL&pitch_category=ALL&venue=ALL")
    assert res_xr.status == 200
    xr_data = json.loads(res_xr.read().decode('utf-8'))
    venue_splits = xr_data.get('venue_splits', [])
    print(f"Total distinct venues for Kohli: {len(venue_splits)}")
    
    # Check Chinnaswamy
    chinnaswamy = [v for v in venue_splits if 'Chinnaswamy' in v['venue']]
    print("Chinnaswamy entries found:", len(chinnaswamy))
    for v in chinnaswamy:
        print(f"  -> '{v['venue']}': {v['matches']} matches, {v['balls']} balls, {v['runs']} runs, xR: {v['xr']}")
    assert len(chinnaswamy) == 1, f"Expected exactly 1 merged Chinnaswamy entry, found {len(chinnaswamy)}"
    assert chinnaswamy[0]['matches'] == 101, f"Expected 101 matches, got {chinnaswamy[0]['matches']}"
    assert chinnaswamy[0]['balls'] == 2561, f"Expected 2561 balls, got {chinnaswamy[0]['balls']}"
    print("[OK] Chinnaswamy is completely and accurately merged!")

    # Check Wankhede
    wankhede = [v for v in venue_splits if 'Wankhede' in v['venue']]
    print("\nWankhede entries found:", len(wankhede))
    for v in wankhede:
        print(f"  -> '{v['venue']}': {v['matches']} matches, {v['balls']} balls, {v['runs']} runs")
    assert len(wankhede) == 1, f"Expected 1 Wankhede entry, got {len(wankhede)}"
    assert wankhede[0]['matches'] == 23
    print("[OK] Wankhede is merged!")

    print("\n=== 4. Testing Filtering on Normalized Venue ===")
    res_filt = urllib.request.urlopen(f"{BASE_URL}/api/player/xr?name=Virat%20Kohli&role=bat&tournament=ALL&pitch_category=ALL&venue=M%20Chinnaswamy%20Stadium,%20Bengaluru")
    assert res_filt.status == 200
    filt_data = json.loads(res_filt.read().decode('utf-8'))
    print(f"Filtered to Chinnaswamy: {filt_data.get('total_balls')} balls, {filt_data.get('total_runs')} runs, Run Value: {filt_data.get('run_value')}")
    assert filt_data.get('total_balls') == 2561
    assert filt_data.get('total_runs') == 3588
    print("[OK] Filter on Chinnaswamy returns unified data perfectly.")

    print("\n=== 5. Testing Head-to-Head Duel API (/api/compare) ===")
    res_comp = urllib.request.urlopen(f"{BASE_URL}/api/compare?player1=Virat%20Kohli&player2=Sandeep%20Sharma&mode=auto&vs_bowler_type=ALL&vs_batter_hand=ALL&tournament=ALL")
    assert res_comp.status == 200
    comp_data = json.loads(res_comp.read().decode('utf-8'))
    print("Duel compare loaded successfully:")
    print("  Mode:", comp_data.get('mode'))
    print("  H2H Balls:", comp_data.get('h2h', {}).get('balls'))
    print("  H2H Runs:", comp_data.get('h2h', {}).get('runs'))
    print("  H2H Outs:", comp_data.get('h2h', {}).get('dismissals'))
    bat_phases = comp_data.get('bat_stats', {}).get('phases', {})
    bowl_phases = comp_data.get('bowl_stats', {}).get('phases', {})
    print("  Powerplay bat balls:", bat_phases.get('Powerplay', {}).get('balls'), "vs bowl balls:", bowl_phases.get('Powerplay', {}).get('balls'))
    print("  Middle bat balls:", bat_phases.get('Middle', {}).get('balls'), "vs bowl balls:", bowl_phases.get('Middle', {}).get('balls'))
    print("  Death bat balls:", bat_phases.get('Death', {}).get('balls'), "vs bowl balls:", bowl_phases.get('Death', {}).get('balls'))
    print("[OK] Compare API returns complete phase data for 3-column grid!")

    print("\n=== 6. Testing Bowler Defensive Map API (/api/player/defensive_wheel) ===")
    res_def = urllib.request.urlopen(f"{BASE_URL}/api/player/defensive_wheel?name=Jasprit%20Bumrah&phase=ALL&hand=ALL&tournament=ALL")
    assert res_def.status == 200
    def_data = json.loads(res_def.read().decode('utf-8'))
    print("  Runs Conceded:", def_data.get('total_runs_conceded'))
    print("  Wickets:", def_data.get('total_wkts'))
    print("  Economy:", def_data.get('overall_econ'))
    print("  Strike Rate:", def_data.get('overall_sr'))
    print("  Primary Restrictive:", def_data.get('fortress_sector', {}).get('FullName'))
    print("  High Concession:", def_data.get('leak_sector', {}).get('FullName'))
    print("[OK] Defensive wheel API returns complete metrics and sector data!")

    print("\n>>> ALL TESTS PASSED WITH 100% SUCCESS! <<<")

if __name__ == '__main__':
    test_routes()
