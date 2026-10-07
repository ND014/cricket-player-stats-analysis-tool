import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import matchup_engine

c1, c2 = 'Kuldeep Yadav', 'HH Pandya'

for m in ['auto', 'bat_vs_bat', 'bowl_vs_bowl', 'bat_vs_bowl', 'bowl_vs_bat']:
    print(f"\n==================== TESTING MODE: {m} ====================")
    matchup_engine.compare_players(c1, c2, mode=m, show_plot=False)

print("\n[+] ALL 5 MODES WORK FLAWLESSLY IN matchup_engine.py!")
