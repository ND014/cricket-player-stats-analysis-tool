import json

# Test queries
test_queries = [
    'david miller',
    'tim david',
    'd miller',
    'th david',
    'v kohli',
    'virat kohli',
    'kl rahul',
    'a sharma',
    'abhishek sharma',
    'bumrah',
    'jj bumrah',
    'hitman',
    'boom boom',
    'surya',
    'de villiers',
    'abd',
    'maxwell'
]

import sys
sys.path.insert(0, '.')
import scratch.test_master_registry as mr

registry = mr.registry

def search(q, limit=5):
    q = q.strip().lower()
    exact = []
    prefix_full = []
    prefix_cric = []
    prefix_alias = []
    substr_full = []
    substr_alias = []

    seen = set()
    for r in registry:
        cric = r['cric_name']
        full = r['full_name'].lower()
        cric_l = cric.lower()
        aliases = r['aliases']

        if q == full or q == cric_l or q in aliases:
            if cric not in seen:
                exact.append(r)
                seen.add(cric)
        elif full.startswith(q):
            if cric not in seen:
                prefix_full.append(r)
                seen.add(cric)
        elif cric_l.startswith(q):
            if cric not in seen:
                prefix_cric.append(r)
                seen.add(cric)
        elif any(a.startswith(q) for a in aliases):
            if cric not in seen:
                prefix_alias.append(r)
                seen.add(cric)
        elif q in full or q in cric_l:
            if cric not in seen:
                substr_full.append(r)
                seen.add(cric)
        elif any(q in a for a in aliases):
            if cric not in seen:
                substr_alias.append(r)
                seen.add(cric)

    ordered = exact + prefix_full + prefix_cric + prefix_alias + substr_full + substr_alias
    return ordered[:limit]

print("=== SEARCH BENCHMARK ===")
for q in test_queries:
    res = search(q, limit=3)
    displays = [r['display'] for r in res]
    print(f"Query: '{q:<16}' -> {displays}")
