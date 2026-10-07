"""
Generator script for the Global T20 Matchup, Wagon Wheel & Skill Analytics Notebook.
Features 2.67M deliveries across 10,859 matches in 18 world tournaments.
"""

import json

cells = []

def add_md(source):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    })

def add_code(source):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.split("\n")]
    })

# ------------------------------------------------------------------------------
# Cell 1: Master Title & Project Blueprint
# ------------------------------------------------------------------------------
add_md("""# 🏏 Global T20 Matchup, Wagon Wheel & Skill Analytics Engine
### Pro-Franchise Sports Analytics, Tactical Scouting & Player Comparison Across Worldwide T20 Cricket
**Data Source**: Official Cricsheet Historical Deliveries Database
* **Total Matches**: **10,859 matches** across **18 premier world tournaments**
* **Total Deliveries**: **2,671,062 ball-by-ball rows**
* **Total Players Covered**: **7,820 Batters | 5,833 Bowlers worldwide**
* **Worldwide Domestic & Franchise Leagues Included**:
  * 🇮🇳 **India**: Indian Premier League (`IPL`), Syed Mushtaq Ali Trophy (`SMAT`)
  * 🌍 **International**: Men's T20 Internationals (`T20I`), ICC Men's T20 World Cup (`T20_WORLD_CUP`)
  * 🇦🇺 **Australia**: Big Bash League (`BBL`)
  * 🇵🇰 **Pakistan**: Pakistan Super League (`PSL`)
  * 🏝️ **West Indies**: Caribbean Premier League (`CPL`)
  * 🇿🇦 **South Africa**: SA20 (`SA20`), CSA T20 Challenge (`CSA_T20`), Mzansi Super League (`MSL`)
  * 🇱🇰 **Sri Lanka**: Lanka Premier League (`LPL`), Major Clubs T20 Tournament (`SL_CLUBS_T20`)
  * 🇳🇿 **New Zealand**: Super Smash (`SUPER_SMASH`)
  * 🏴󠁧󠁢󠁥󠁮󠁧󠁿 **England**: T20 Blast (`T20_BLAST`), The Hundred (`THE_HUNDRED`)
  * 🇧🇩 **Bangladesh**: Bangladesh Premier League (`BPL`)
  * 🇺🇸 **USA**: Major League Cricket (`MLC`)
  * 🇦🇪 **UAE**: International League T20 (`ILT20`)

---
### 📌 Executive Overview: Pure Skill-Based Data Analytics
This platform moves away from macroeconomic auction pricing to provide **deep tactical data analytics**:
1. **Interactive Wagon Wheel for Batters**: 8-sector radial scoring distribution with percentage of runs scored, shot trajectories (1s/2s, 4s, 6s), and **dynamic filtering vs specific bowler archetypes** (`LAF`, `SLA`, `WRIST_SPIN`, etc.).
2. **Defensive Radial Wheel for Bowlers**: The defensive counterpart—showing where batters score runs, boundary leaks, defensive fortress zones, and **Wicket Dismissal Hotspots**.
3. **Head-to-Head Player Comparison (`compare_players`)**: Side-by-side scouting dossier comparing any two players (Batter vs Batter, Bowler vs Bowler, or Batter vs Bowler Duel) with historical head-to-head match-up records.
4. **Top 3 Nemesis Bowlers & Punisher Batters**: Mathematical discovery of who troubles a batter most and who attacks a bowler most.
5. **Domestic Moneyball Tactical Alternatives**: Scouting uncapped gems (SMAT, CSA T20) matching or exceeding marquee benchmarks in dominant phases.""")

# ------------------------------------------------------------------------------
# Cell 2: Step 1 - Environment & Imports
# ------------------------------------------------------------------------------
add_md("""## 1. Environment & Global Database Setup
We connect to our master SQLite database (`data/global_t20.db`) containing indexed tables of all **2,671,062 deliveries**.""")

add_code("""import os
import sys
import sqlite3
import importlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set working directory to project root
project_dir = os.path.abspath(os.getcwd())
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Ensure matchup_engine is freshly reloaded even if Jupyter kernel was kept alive from an earlier session
if 'matchup_engine' in sys.modules:
    import matchup_engine
    importlib.reload(matchup_engine)

from matchup_engine import (
    audit_player,
    compare_players,
    plot_batter_wagon_wheel,
    get_batter_wagon_data,
    plot_bowler_defensive_wheel,
    get_bowler_defensive_wagon_data,
    find_cost_effective_alternatives,
    get_top_nemesis_bowlers,
    get_top_punisher_batters,
    resolve_player_name,
    GLOBAL_TOURNAMENTS,
    INDIAN_PLAYER_METADATA,
    get_player_deliveries,
    get_t20_db_connection
)

pd.set_option('display.max_columns', 35)
pd.set_option('display.width', 1000)
pd.set_option('display.precision', 2)

conn = get_t20_db_connection()
print("[+] Master SQLite Global T20 Database connected successfully!")""")

# ------------------------------------------------------------------------------
# Cell 3: Step 2 - Database Tournament Census
# ------------------------------------------------------------------------------
add_md("""## 2. Master Global T20 Database Census
Let's query the 18 global tournaments and inspect the exact match and delivery distributions across domestic leagues and international cricket.""")

add_code("""tourn_df = pd.read_sql(\"\"\"
SELECT 
    tournament AS Tournament,
    COUNT(DISTINCT match_id) AS Matches,
    COUNT(*) AS Deliveries,
    COUNT(DISTINCT striker) AS Batters,
    COUNT(DISTINCT bowler) AS Bowlers,
    MIN(start_date) AS Earliest_Match,
    MAX(start_date) AS Latest_Match
FROM deliveries
GROUP BY tournament
ORDER BY Deliveries DESC
\"\"\", conn)

print(f"Total Tournaments: {len(tourn_df)} | Total Matches: {tourn_df['Matches'].sum():,} | Total Deliveries: {tourn_df['Deliveries'].sum():,}")
tourn_df""")

# ------------------------------------------------------------------------------
# Cell 4: Step 3 - Interactive Batter Wagon Wheel (Overall vs Bowler Archetype)
# ------------------------------------------------------------------------------
add_md("""## 3. Interactive Batter Wagon Wheel (Overall vs By Bowler Type)
The wagon wheel divides the cricket field into **8 standard sectors**:
`Cover / Extra Cover`, `Point`, `Third Man`, `Fine Leg`, `Square Leg`, `Midwicket / Cow Corner`, `Long On`, and `Long Off`.
* Automatically detects stance (`RHB` vs `LHB`) and mirrors off-side and leg-side.
* Calculates the exact **percentage of total runs scored in each sector**.
* **Archetype Selector (`vs_bowler_type`)**: Filter by `'ALL'`, `'LAF'` (Left-Arm Pace), `'SLA'` (Left-Arm Spin), `'WRIST_SPIN'`, `'OFF_SPIN'`, `'RAF'` (Right-Arm Fast).
* Let's compare Virat Kohli's overall wagon wheel vs his wagon wheel against his primary kryptonite: Slow Left-Arm Orthodox (`SLA`)!""")

add_code("""# 1. Overall Wagon Wheel for Virat Kohli (All Bowlers)
plot_batter_wagon_wheel("Virat Kohli", vs_bowler_type="ALL")

# 2. Dynamic Filter: Virat Kohli vs Left-Arm Orthodox Spin (SLA Kryptonite)
plot_batter_wagon_wheel("Virat Kohli", vs_bowler_type="SLA")""")

# ------------------------------------------------------------------------------
# Cell 5: Step 4 - Bowler Defensive Field Distribution & Sector Analysis
# ------------------------------------------------------------------------------
add_md("""## 4. Bowler Defensive Field Distribution & Wicket Dismissal Hotspots
The defensive counterpart to the wagon wheel for bowlers:
* Shows **where opponents score runs off this bowler** across the 8 field sectors.
* Identifies **Primary Restrictive Sectors** (where the bowler suppresses runs and boundaries) vs **High-Concession Sectors** (where batters hit boundaries).
* Visualizes **Wicket Dismissal Hotspots** (with clean markers showing where catches and dismissals were induced in the field).
* Filterable by `phase` (`'Powerplay'`, `'Middle'`, `'Death'`) and `vs_batter_hand` (`'RHB'`, `'LHB'`).
* Let's audit Jasprit Bumrah's defensive execution in the **Death Overs (overs 16–20)**!""")

add_code("""# Defensive Field Distribution: Jasprit Bumrah in the Death Overs
plot_bowler_defensive_wheel("Jasprit Bumrah", phase="Death")""")

# ------------------------------------------------------------------------------
# Cell 6: Step 5 - Head-to-Head Player Comparison Engine (`compare_players`)
# ------------------------------------------------------------------------------
add_md("""## 5. Pro-Franchise Player Comparison Engine (`compare_players`)
Compare **ANY two cricketers worldwide** with zero hardcoding:
* **Role-Aware**: Automatically compares Batters vs Batters, Bowlers vs Bowlers, All-Rounders vs All-Rounders, or direct Batter vs Bowler duels.
* **Filter by Bowler Archetype (`vs_bowler_type`)**: Deep-dive comparisons against specific bowler styles (e.g. `'RAF'`, `'LAF'`, `'SLA'`, `'WRIST_SPIN'`, `'PACE'`, `'SPIN'`).
* **Phase Performance Breakdown**: Side-by-side Powerplay, Middle, and Death metrics with par reference benchmarks.
* **Direct Head-to-Head Duel**: If player 1 and player 2 ever faced each other in the 2.67M ball database, extracts their exact historical head-to-head record (Balls, Runs, Dismissals, Strike Rate, Dot %, Boundaries)!""")

add_code("""# A. Batter Comparison vs Bowler Archetype: Virat Kohli vs Shubman Gill (against Right-Arm Fast RAF)
compare_players("Virat Kohli", "Shubman Gill", vs_bowler_type="RAF")

# B. Batter Comparison vs Left-Arm Pace (LAF): Virat Kohli vs Shubman Gill
compare_players("Virat Kohli", "Shubman Gill", vs_bowler_type="LAF")

# C. World #1 Bowler Comparison: Jasprit Bumrah vs Rashid Khan
compare_players("Jasprit Bumrah", "Rashid Khan")

# D. Batter vs Nemesis Bowler Direct Duel: Virat Kohli vs Sandeep Sharma
compare_players("Virat Kohli", "Sandeep Sharma")""")

# ------------------------------------------------------------------------------
# Cell 7: Step 6 - Case Study 1: Nicholas Pooran (Global T20 Disruptor)
# ------------------------------------------------------------------------------
add_md("""## 6. Case Study 1: Nicholas Pooran (Global 360-Degree Disruptor)
Let's audit **Nicholas Pooran** across all 12 global competitions he has played in:
* What is his multi-tournament footprint (IPL, CPL, MLC, The Hundred, ILT20)?
* Who are his **Top 3 Nemesis Bowlers** who stifle his boundary scoring and induce dismissals?
* Which domestic SMAT prospects offer matching middle-order firepower?""")

add_code("""audit_player("N Pooran", tournament='ALL')""")

# ------------------------------------------------------------------------------
# Cell 8: Step 7 - Case Study 2: Andre Russell (Dual All-Rounder Audit)
# ------------------------------------------------------------------------------
add_md("""## 7. Case Study 2: Andre Russell (Dual All-Rounder Audit: Nemeses & Punishers)
All-rounders must be evaluated across both disciplines simultaneously:
* **Batting Discipline**: 10,300+ career runs across 14 tournaments at 168+ Strike Rate.
  * Who are his **Top 3 Nemesis Bowlers** who contain his power (wrist spin)?
* **Bowling Discipline**: 567 career wickets in 1,567 overs.
  * Who are the **Top 3 Punisher Batters** who damage his bowling?
* What are the phase-specific domestic alternatives for his death-finishing role?""")

add_code("""audit_player("Andre Russell", tournament='ALL')""")

# ------------------------------------------------------------------------------
# Cell 9: Step 8 - Case Study 3: Domestic SMAT Scouting (Arzan Nagwaswalla)
# ------------------------------------------------------------------------------
add_md("""## 8. Case Study 3: Arzan Nagwaswalla (Pure Domestic SMAT Gem)
Let's audit **Arzan Nagwaswalla** in the Syed Mushtaq Ali Trophy:
* As an uncapped Indian left-arm pacer (`LAF`), what are his Powerplay economy and death wicket numbers?
* Can domestic talent serve as a high-value, cost-effective replacement for marquee pacers?""")

add_code("""audit_player("Arzan Nagwaswalla", tournament='SMAT')""")

# ------------------------------------------------------------------------------
# Cell 10: Step 9 - Interactive Global Terminal: Audit ANY Player Worldwide
# ------------------------------------------------------------------------------
add_md("""## 9. Interactive Global Scouting Terminal: Audit ANY Player in the World!
Our database covers **7,820 Batters and 5,833 Bowlers across 18 competitions**. None of them need to be hardcoded!
The engine automatically handles:
1. **Dynamic Name Resolution**: Full names, surnames, or initials (e.g. `'Heinrich Klaasen'`, `'Wanindu Hasaranga'`, `'Suryakumar Yadav'`).
2. **Role & Position Inference**: Automatically identifies Batter, Bowler, or All-Rounder from career ball volumes.
3. **Nemesis & Punisher Discovery**: Instantly computes top 3 antagonists based on dismissals, strike rates, and boundary percentages.
4. **Wagon Wheel & Player Comparison**: Call `plot_batter_wagon_wheel(...)`, `plot_bowler_defensive_wheel(...)`, or `compare_players(...)` on anyone!""")

add_code("""# Audit ANY cricketer worldwide across 18 leagues - zero hardcoding required!
audit_player("Heinrich Klaasen", tournament='ALL')""")

# ------------------------------------------------------------------------------
# Cell 11: Step 10 - Head-to-Head Duels & Contextual Archetype Comparisons
# ------------------------------------------------------------------------------
add_md("""## 10. Head-to-Head Duels & Contextual Archetype Comparisons
The comparison engine intelligently filters context based on the discipline:
* **Batter vs Batter**: Filters by opponent bowler archetype (e.g. Right-Arm Fast `RAF`, Left-Arm Fast `LAF`, Wrist Spin, etc.).
* **Bowler vs Bowler**: Filters by opponent batter stance (`LHB` Left-Handed vs `RHB` Right-Handed).
* **Batter vs Bowler**: Direct 1-on-1 Head-to-Head duel record with real-life ball-by-ball log.""")

add_code("""# 1. Batter vs Batter benchmark against Right-Arm Fast (RAF)
compare_players("Virat Kohli", "Shubman Gill", mode='bat_vs_bat', vs_bowler_type='RAF')

# 2. Bowler vs Bowler benchmark against Left-Handed Batters (LHB)
compare_players("Jasprit Bumrah", "Rashid Khan", mode='bowl_vs_bowl', vs_batter_hand='LHB')

# 3. Direct Head-to-Head Duel: Historical ball-by-ball duel
compare_players("Virat Kohli", "Sandeep Sharma", mode='auto')""")

# Compile into Jupyter Notebook JSON
notebook_dict = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.9"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

nb_filename = "IPL_Matchup_and_Value_Audit.ipynb"
with open(nb_filename, "w", encoding="utf-8") as f:
    json.dump(notebook_dict, f, indent=2)

print(f"[+] Successfully compiled Global T20 notebook: {nb_filename}")
