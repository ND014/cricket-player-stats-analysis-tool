import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_url(url, name):
    print(f"Testing {name}: {url} ...", end=" ")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TestClient'})
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read()
            if "application/json" in resp.headers.get('Content-Type', ''):
                data = json.loads(content.decode('utf-8'))
                print(f"SUCCESS [HTTP {status}] - Keys: {list(data.keys())[:5]}")
                return data
            else:
                print(f"SUCCESS [HTTP {status}] - Bytes: {len(content)}")
                return content
    except Exception as e:
        print(f"FAILED: {e}")
        return None

print("=== VERIFYING EXPECTED RUNS & PITCH VALUE AUDIT ENDPOINTS ===\n")

# 1. Audit Endpoint for Virat Kohli
audit_vk = test_url(f"{BASE_URL}/api/player/audit?name=Virat%20Kohli&tournament=ALL", "Virat Kohli Audit")
assert audit_vk is not None
assert 'batting_xr' in audit_vk
assert audit_vk['batting_xr']['run_value'] is not None
print(f"  -> Virat Kohli Career Run Value: {audit_vk['batting_xr']['run_value']} runs")
print(f"  -> Pitch tiers returned: {[p['category'] for p in audit_vk['batting_xr']['pitch_splits']]}")

# 2. xR Batting Endpoint for Heinrich Klaasen
xr_hk = test_url(f"{BASE_URL}/api/player/xr?name=H%20Klaasen&role=bat&tournament=IPL", "Heinrich Klaasen IPL xR")
assert xr_hk is not None
print(f"  -> Klaasen IPL Run Value: {xr_hk['run_value']:+0.1f} | Actual SR: {xr_hk['actual_sr']} vs Expected: {xr_hk['expected_sr']} | Impact: {xr_hk['impact_ratio']}x")
print(f"  -> Image B64 length: {len(xr_hk.get('image_b64', ''))}")

# 3. xR Bowling Endpoint for Jasprit Bumrah
xr_bum = test_url(f"{BASE_URL}/api/player/xr?name=JJ%20Bumrah&role=bowl&tournament=ALL", "Jasprit Bumrah xRC")
assert xr_bum is not None
print(f"  -> Bumrah Runs Saved: +{xr_bum['runs_saved']:.1f} runs | Actual Econ: {xr_bum['actual_econ']} vs Par: {xr_bum['expected_econ']}")
print(f"  -> Top defensive match: {xr_bum['top_innings'][0]['venue']} (+{xr_bum['top_innings'][0]['runs_saved']} runs saved)")

# 4. Compare Endpoint with xR integration (Kohli vs Rohit)
comp = test_url(f"{BASE_URL}/api/compare?player1=Virat%20Kohli&player2=Rohit%20Sharma&mode=bat_vs_bat&tournament=ALL", "Kohli vs Rohit Comparison")
assert comp is not None
assert 'xr1' in comp and 'xr2' in comp
print(f"  -> Kohli xR Run Value: {comp['xr1']['run_value']:+0.1f} | Rohit xR Run Value: {comp['xr2']['run_value']:+0.1f}")

# 5. Compare Bowlers (Bumrah vs Rashid)
comp_bowl = test_url(f"{BASE_URL}/api/compare?player1=JJ%20Bumrah&player2=Rashid%20Khan&mode=bowl_vs_bowl&tournament=ALL", "Bumrah vs Rashid Comparison")
assert comp_bowl is not None
assert 'xr1' in comp_bowl and 'xr2' in comp_bowl
print(f"  -> Bumrah Runs Saved: +{comp_bowl['xr1']['runs_saved']:.1f} | Rashid Runs Saved: +{comp_bowl['xr2']['runs_saved']:.1f}")

print("\nALL VERIFICATIONS PASSED 100% PERFECTLY!")
