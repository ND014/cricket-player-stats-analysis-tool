import sqlite3
import pandas as pd
import matchup_engine

c1, c2 = 'Kuldeep Yadav', 'HH Pandya'

print("--- MODE 1: bat_vs_bat ---")
matchup_engine.compare_players(c1, c2, mode='bat_vs_bat', show_plot=False)

print("\n--- MODE 2: bowl_vs_bowl ---")
# Currently matchup_engine doesn't have mode parameter yet, let's see what happens
try:
    matchup_engine.compare_players(c1, c2, mode='bowl_vs_bowl', show_plot=False)
except TypeError as e:
    print("Expected TypeError before updating:", e)
