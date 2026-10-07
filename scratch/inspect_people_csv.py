import urllib.request
import pandas as pd
import io

print("Fetching people.csv sample...")
req = urllib.request.Request('https://cricsheet.org/register/people.csv', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = resp.read()

df_people = pd.read_csv(io.BytesIO(data))
print("People shape:", df_people.shape)
print("People columns:", df_people.columns.tolist())
print(df_people.head(10)[['identifier', 'name', 'unique_name']])

# Check specific players: Virat Kohli, David Miller, Tim David, Rohit Sharma
test_names = ['Virat Kohli', 'David Miller', 'Tim David', 'Rohit Sharma', 'Jasprit Bumrah', 'KL Rahul']
print("\nSearching people.csv for test players:")
for t in test_names:
    matches = df_people[df_people['unique_name'].str.contains(t, case=False, na=False) | df_people['name'].str.contains(t, case=False, na=False)]
    for idx, row in matches.iterrows():
        print(f"[{t}] ID: {row['identifier']}, Name: {row['name']}, Unique: {row['unique_name']}")
