import urllib.request
import json

c1, c2 = 'Kuldeep Yadav', 'Hardik Pandya'
modes = ['auto', 'bowl_vs_bowl', 'bowl_vs_bat', 'bat_vs_bowl', 'bat_vs_bat']

for m in modes:
    u = f"http://127.0.0.1:5000/api/compare?player1={urllib.parse.quote(c1)}&player2={urllib.parse.quote(c2)}&mode={m}&tournament=ALL"
    r = urllib.request.urlopen(u)
    data = json.loads(r.read().decode('utf-8'))
    print(f"[{r.status} OK] Mode: {m:<15} -> Resolved Mode: {data['mode']:<15} | Comparison Type: {data['comparison_type']:<22} | Has H2H: {data['has_h2h']}")

print("\nAll comparison modes verified via Flask API successfully!")
