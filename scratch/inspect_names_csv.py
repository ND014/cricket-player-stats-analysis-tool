import urllib.request
import pandas as pd
import io

print("Fetching names.csv...")
req = urllib.request.Request('https://cricsheet.org/register/names.csv', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as resp:
    data_names = resp.read()

df_names = pd.read_csv(io.BytesIO(data_names))
print("Names shape:", df_names.shape)
print("Names head:\n", df_names.head(10))

# Test players in names.csv
for p in ['Kohli', 'Miller', 'David', 'Klaasen', 'Bumrah', 'Sharma', 'Rahul', 'Maxwell']:
    m = df_names[df_names['name'].str.contains(p, case=False, na=False)]
    print(f"\n--- Matches for '{p}' ({len(m)} rows) ---")
    print(m.head(8))
