import urllib.request
import urllib.parse
import json

def test_search(q):
    url = f'http://127.0.0.1:5000/api/search?q={urllib.parse.quote(q)}&limit=5'
    res = urllib.request.urlopen(url)
    items = json.loads(res.read())
    displays = [i['display'] for i in items]
    print(f"Search [{q:<15}] -> {displays}")

def test_audit(name):
    url = f'http://127.0.0.1:5000/api/player/audit?name={urllib.parse.quote(name)}'
    res = urllib.request.urlopen(url)
    data = json.loads(res.read())
    full = data.get('full_name')
    cric = data.get('cric_name')
    delivs = data.get('total_deliveries')
    print(f"Audit  [{name:<15}] -> Full: {full:<16} | Cric: {cric:<12} | Deliveries: {delivs}")

print("=== SEARCH ENDPOINT TESTS ===")
test_search('david miller')
test_search('d miller')
test_search('tim david')
test_search('th david')
test_search('v kohli')
test_search('kl rahul')
test_search('a sharma')
test_search('bumrah')
test_search('jj bumrah')

print("\n=== AUDIT ENDPOINT TESTS ===")
test_audit('David Miller')
test_audit('d miller')
test_audit('Tim David')
test_audit('th david')
test_audit('Virat Kohli')
test_audit('v kohli')
test_audit('KL Rahul')
test_audit('kl rahul')
test_audit('Abhishek Sharma')

def test_comp(p1, p2):
    url = f'http://127.0.0.1:5000/api/compare?player1={urllib.parse.quote(p1)}&player2={urllib.parse.quote(p2)}&mode=auto'
    res = urllib.request.urlopen(url)
    data = json.loads(res.read())
    p1_d = data['player1']['display_name']
    p2_d = data['player2']['display_name']
    print(f"Compare [{p1} vs {p2}] -> {p1_d} vs {p2_d} | CompType: {data['comparison_type']}")

print("\n=== COMPARE ENDPOINT TESTS ===")
test_comp('David Miller', 'Tim David')
test_comp('d miller', 'th david')
test_comp('kl rahul', 'v kohli')
test_comp('abhishek sharma', 'bumrah')
