import urllib.request

urls = [
    'http://127.0.0.1:5000/',
    'http://127.0.0.1:5000/static/css/style.css',
    'http://127.0.0.1:5000/static/js/app.js',
    'http://127.0.0.1:5000/api/tournaments',
    'http://127.0.0.1:5000/api/census',
    'http://127.0.0.1:5000/api/player/audit?name=Rashid%20Khan',
    'http://127.0.0.1:5000/api/player/wagon?name=Virat%20Kohli&bowler_type=SLA',
    'http://127.0.0.1:5000/api/player/defensive_wheel?name=Jasprit%20Bumrah&phase=Death&hand=LHB',
    'http://127.0.0.1:5000/api/compare?player1=Virat%20Kohli&player2=Jasprit%20Bumrah'
]

for u in urls:
    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req)
    content = res.read()
    endpoint = u.replace('http://127.0.0.1:5000', '')
    print(f"[{res.status} OK] {endpoint[:55]:<55} | Size: {len(content):,} bytes")

print("\nAll routes verified successfully!")
