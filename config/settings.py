"""
Configuration settings, archetypes, phase boundaries, and valuation parameters
for the IPL Auction Matchup & Value Audit.
"""

# ==============================================================================
# 1. MATCH PHASES (Over indices: 0 to 19)
# ==============================================================================
PHASE_POWERPLAY = "Powerplay"  # Overs 0-5  (1st to 6th over)
PHASE_MIDDLE = "Middle"        # Overs 6-14 (7th to 15th over)
PHASE_DEATH = "Death"          # Overs 15-19 (16th to 20th over)

PHASE_OVER_RANGES = {
    PHASE_POWERPLAY: (0, 5),
    PHASE_MIDDLE: (6, 14),
    PHASE_DEATH: (15, 19),
}

# ==============================================================================
# 2. BATTER POSITIONS (Position-based classification)
# ==============================================================================
BATTER_POSITIONS = [
    "TOP_ORDER",       # Batting Nos. 1-3 (Openers & No. 3)
    "MIDDLE_ORDER",    # Batting Nos. 4-5 (Middle Order Stabilizers & Accelerators)
    "FINISHER",        # Batting Nos. 6-8 (Finishers & Death-Overs Hitters)
    "TAILENDER",       # Batting Nos. 9-11 (Lower Order / Tailenders)
]

# ==============================================================================
# 3. BOWLER TACTICAL ARCHETYPES (8 Pro-Franchise Categories)
# ==============================================================================
BOWLER_ARCHETYPES = [
    # Pace
    "RAF",              # Right-Arm Fast / Express (>140 kph - Bumrah, Nortje)
    "RAM",              # Right-Arm Medium / Cutters (120-135 kph - Harshal, Sandeep)
    "LAF",              # Left-Arm Fast / Express (>140 kph - Starc, Boult)
    "LAM",              # Left-Arm Medium / Cutters (118-132 kph - Mustafizur, Natarajan)
    
    # Spin
    "OFF_SPIN",         # Right-Arm Finger Spin (Ashwin, Washington Sundar)
    "WRIST_SPIN",       # Right-Arm Leg-Break / Mystery (Rashid Khan, Chahal, Bishnoi)
    "SLA",              # Slow Left-Arm Orthodox (Axar Patel, Jadeja, Maharaj)
    "LEFT_WRIST_SPIN",  # Left-Arm Chinaman / Unorthodox (Kuldeep Yadav, Noor Ahmad)
]

# ==============================================================================
# 4. PLAYER PRIMARY ROLES & ALL-ROUNDER TYPES
# ==============================================================================
ROLE_BATTER = "Batter"
ROLE_BOWLER = "Bowler"
ROLE_ALL_ROUNDER = "All-Rounder"

PLAYER_ROLES = [ROLE_BATTER, ROLE_BOWLER, ROLE_ALL_ROUNDER]

AR_TYPE_BATTING = "Batting All-Rounder"  # Top/Middle batter who chips in overs
AR_TYPE_BOWLING = "Bowling All-Rounder"  # Primary bowler who provides late cameos
AR_TYPE_TRUE = "True All-Rounder"        # Genuine 4-over bowler & Top-6 batter

# ==============================================================================
# 5. METRIC WEIGHTS & PARAMETERS
# ==============================================================================
# Kryptonite Vulnerability Index (KVI) weights for batters
# Quantifies drop-off against a specific bowler archetype relative to baseline
BATTER_KVI_WEIGHTS = {
    "sr_drop": 0.45,       # Drop in Strike Rate
    "hazard_rate": 0.35,   # Increase in Dismissal Hazard (Balls per Dismissal drop)
    "dot_rate": 0.20,      # Dot ball percentage faced
}

# Kryptonite Vulnerability Index (KVI) weights for bowlers
# Quantifies leakage against specific batter positions or opposite-hand batters
BOWLER_KVI_WEIGHTS = {
    "econ_leak": 0.50,     # Economy rate inflation
    "strike_decay": 0.30,  # Bowling Strike Rate decay (inability to take wickets)
    "boundary_leak": 0.20, # Boundary concession rate
}

# Dot-Ball Pressure Score (DBPS) weights
DBPS_WEIGHTS = {
    "dot_ball_pct": 0.60,
    "strike_rotation_deficit": 0.40,  # 100 - Strike Rotation Index
}

# Phase Leverage Multipliers for Match Outcomes
# Runs and wickets in Death carry higher leverage in T20 match outcomes
PHASE_RUN_WEIGHTS = {
    PHASE_POWERPLAY: 1.15,
    PHASE_MIDDLE: 1.00,
    PHASE_DEATH: 1.40,
}

PHASE_WICKET_WEIGHTS = {
    PHASE_POWERPLAY: 1.25,
    PHASE_MIDDLE: 1.00,
    PHASE_DEATH: 1.35,
}

# Valuation Model Parameters (INR Crores)
BASE_RESERVE_PRICE = 0.5   # Base minimum IPL reserve (50 Lakhs)
MAX_PURSE_BENCHMARK = 25.0 # Max price ceiling for top marquee in auction

# Directories
OUTPUT_DIR = "outputs"
DATA_DIR = "data"
