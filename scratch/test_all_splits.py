import urllib.request
import urllib.parse
import json

def test(name, role, **kwargs):
    qs = '&'.join([f"{k}={v}" for k, v in kwargs.items()])
    url = f"http://127.0.0.1:5000/api/player/splits?name={urllib.parse.quote(name)}&role={role}&{qs}"
    req = urllib.request.urlopen(url)
    data = json.loads(req.read())
    s = data['summary']
    if role == 'bat':
        types_str = ', '.join(data['selected_types'])
        print(f"OK: {name} [BAT] vs [{types_str}]: {s['runs']}r ({s['balls']}b), {s['dismissals']} outs, {s['sr']} SR, {s['dot_pct']}% dots")
    else:
        hands_str = ', '.join(data['selected_hands'])
        phases_str = ', '.join(data['selected_phases'])
        print(f"OK: {name} [BOWL] vs [{hands_str}] in [{phases_str}]: {s['wickets']} wkts in {s['overs']} ov ({s['runs']}r), {s['econ']} Econ, {s['dot_pct']}% dots")

print("--- Testing Batter Splits ---")
test('Virat Kohli', 'bat', types='ALL')
test('Virat Kohli', 'bat', types='LAF,RAF')
test('Virat Kohli', 'bat', types='SLA,OFF_SPIN')
test('Virat Kohli', 'bat', types='WRIST_SPIN')
test('Heinrich Klaasen', 'bat', types='SLA,OFF_SPIN,WRIST_SPIN,LEFT_WRIST_SPIN')

print("\n--- Testing Bowler Splits ---")
test('Jasprit Bumrah', 'bowl', hands='ALL', phases='ALL')
test('Jasprit Bumrah', 'bowl', hands='LHB', phases='ALL')
test('Jasprit Bumrah', 'bowl', hands='RHB', phases='ALL')
test('Jasprit Bumrah', 'bowl', hands='ALL', phases='Death')
test('Kuldeep Yadav', 'bowl', hands='LHB', phases='Middle')

print("\n--- Testing All-Rounder Splits ---")
test('Hardik Pandya', 'bat', types='LAF,RAF')
test('Hardik Pandya', 'bowl', hands='LHB', phases='Death')
print("\nALL SPLITS TESTS PASSED SUCCESSFULLY!")
