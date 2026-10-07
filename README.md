# T20 Matchup & Value Audit Engine

A high-performance sports analytics platform and decision-support system for T20 cricket auctions, matchup strategy, and player performance auditing. Built on a historical dataset of **2,671,062 ball-by-ball deliveries** across **18 international and premier domestic leagues worldwide**.

---

## Key Features

### 1. Player Scouting Dossier & Career Phase Efficiency
- Real-time aggregation of runs, balls, strike rates, batting average, dot ball %, and boundary conversion rates.
- Phase breakdown across **Powerplay (Overs 1–6)**, **Middle (Overs 7–15)**, and **Death (Overs 16–20)**.
- **Kryptonite Detection**: Automatically identifies a batter's most vulnerable bowling archetype using the Kryptonite Vulnerability Index (KVI).
- **Nemesis Bowlers & Punisher Batters**: Identifies top individual historical matchups.
- **Moneyball Alternatives (SMAT)**: Finds cost-effective domestic talent matching elite franchise performance benchmarks.

### 2. Tactical Matchup Splits (Multi-Select)
- Interactive multi-selection across 8 bowling archetypes:
  - **Pace**: Right-Arm Fast (`RAF`), Left-Arm Fast (`LAF`), Right-Arm Medium (`RAM`), Left-Arm Medium (`LAM`)
  - **Spin**: Off Spin (`OFF_SPIN`), Wrist Spin (`WRIST_SPIN`), Slow Left-Arm Orthodox (`SLA`), Left-Arm Unorthodox (`LEFT_WRIST_SPIN`)
- Instant comparative visualizations and phase execution bars.

### 3. Interactive Batter Wagon Wheel
- High-resolution sector distribution map visualizing 8 standard field sectors (Cover, Point, Third Man, Fine Leg, Square Leg, Midwicket, Long On, Long Off).
- Real-time filtering by bowler archetype.

### 4. Bowler Defensive Radial Map
- Visualizes run concession density, restrictive fortress sectors, and induced dismissals by field sector.
- Filters across match phases (`All Phases`, `Powerplay`, `Middle`, `Death`) and batter handedness (`RHB`, `LHB`).

### 5. Head-to-Head Duel & Player Comparison
- **Batter vs Batter**: Side-by-side volume, strike rate, average, and archetype performance.
- **Bowler vs Bowler**: Economy rate, dot ball %, bowling strike rate, and stance splits.
- **Batter vs Bowler Duel**: Real-life historical delivery logs and career benchmark comparisons.
- Curated presets and contextual filter dropdowns.

### 6. 18-League Worldwide Census
- Complete dataset covering IPL, SMAT, T20I, T20 World Cup, BBL, PSL, CPL, SA20, CSA T20, MSL, LPL, Sri Lanka Major Clubs, BPL, Super Smash, Vitality T20 Blast, The Hundred, MLC, and ILT20.

---

## Architecture

- **Backend**: Python 3, Flask, Pandas, NumPy, SQLite
- **Visuals**: Matplotlib, Seaborn
- **Frontend**: Vanilla JavaScript (ES6+), Vanilla CSS (glassmorphism design system), semantic HTML5
- **Data Engine**: SQLite database indexing 2.67M deliveries with sub-millisecond phonetic and prefix autocomplete for 8,300+ players

---

## Quickstart

### 1. Installation
```bash
git clone <repository-url>
cd "The IPL Auction Matchup & Value Audit"
pip install -r requirements.txt
```

### 2. Run the Web Application
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your web browser.

### 3. Run the Jupyter Notebook
```bash
jupyter notebook IPL_Matchup_and_Value_Audit.ipynb
```
Or rebuild the notebook anytime using:
```bash
python build_notebook.py
```

---

## License
MIT License. Data sourced from Cricsheet open-data archives.
