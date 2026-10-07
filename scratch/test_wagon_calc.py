import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

SECTORS_RHB = [
    {'name': 'Third Man', 'mid_ang': 315, 'ang_range': (292.5, 337.5), 'offside': True},
    {'name': 'Point', 'mid_ang': 0, 'ang_range': (337.5, 22.5), 'offside': True},
    {'name': 'Cover', 'mid_ang': 45, 'ang_range': (22.5, 67.5), 'offside': True},
    {'name': 'Long Off', 'mid_ang': 78.75, 'ang_range': (67.5, 90), 'offside': True},
    {'name': 'Long On', 'mid_ang': 101.25, 'ang_range': (90, 112.5), 'offside': False},
    {'name': 'Midwicket', 'mid_ang': 135, 'ang_range': (112.5, 157.5), 'offside': False},
    {'name': 'Square Leg', 'mid_ang': 180, 'ang_range': (157.5, 202.5), 'offside': False},
    {'name': 'Fine Leg', 'mid_ang': 225, 'ang_range': (202.5, 247.5), 'offside': False},
]

# Weights for shot distribution
SPIN_WEIGHTS_6 = [0.02, 0.03, 0.12, 0.18, 0.28, 0.30, 0.05, 0.02]
SPIN_WEIGHTS_4 = [0.04, 0.12, 0.24, 0.14, 0.14, 0.20, 0.08, 0.04]
SPIN_WEIGHTS_1 = [0.08, 0.18, 0.20, 0.12, 0.12, 0.15, 0.10, 0.05]

PACE_WEIGHTS_6 = [0.12, 0.08, 0.10, 0.12, 0.20, 0.22, 0.06, 0.10]
PACE_WEIGHTS_4 = [0.18, 0.18, 0.22, 0.10, 0.08, 0.12, 0.06, 0.06]
PACE_WEIGHTS_1 = [0.14, 0.18, 0.18, 0.10, 0.10, 0.12, 0.10, 0.08]

def get_batter_wagon_data(player_name, vs_bowler_type='ALL', tournament='ALL'):
    conn = sqlite3.connect('data/global_t20.db')
    query = "SELECT striker, bowler, bowler_archetype, runs_off_bat, is_boundary, phase, is_wicket, wicket_type FROM deliveries WHERE striker = ?"
    params = [player_name]
    if tournament != 'ALL':
        query += " AND tournament = ?"
        params.append(tournament)
    if vs_bowler_type != 'ALL':
        query += " AND bowler_archetype = ?"
        params.append(vs_bowler_type)
        
    df = pd.read_sql(query, conn, params=params)
    if len(df) == 0:
        return None, df
        
    total_runs = df['runs_off_bat'].sum()
    total_balls = len(df)
    
    # Deterministic simulation based on real delivery rows
    np.random.seed(42) # Consistent repeatable plots
    
    sector_runs = {s['name']: 0 for s in SECTORS_RHB}
    sector_fours = {s['name']: 0 for s in SECTORS_RHB}
    sector_sixes = {s['name']: 0 for s in SECTORS_RHB}
    sector_shots = {s['name']: [] for s in SECTORS_RHB}
    
    is_lhb = False # Default or from metadata
    
    for _, row in df.iterrows():
        r = row['runs_off_bat']
        if r == 0:
            continue
            
        arch = row['bowler_archetype']
        is_spin = arch in ['OFF_SPIN', 'SLA', 'WRIST_SPIN', 'LEFT_WRIST_SPIN']
        
        if r == 6:
            weights = SPIN_WEIGHTS_6 if is_spin else PACE_WEIGHTS_6
        elif r == 4:
            weights = SPIN_WEIGHTS_4 if is_spin else PACE_WEIGHTS_4
        else:
            weights = SPIN_WEIGHTS_1 if is_spin else PACE_WEIGHTS_1
            
        # Select sector based on probabilities
        sec_idx = np.random.choice(len(SECTORS_RHB), p=weights)
        sec = SECTORS_RHB[sec_idx]
        s_name = sec['name']
        
        sector_runs[s_name] += r
        if r == 4:
            sector_fours[s_name] += 1
        elif r == 6:
            sector_sixes[s_name] += 1
            
        # Generate realistic trajectory angle and distance
        ang_min, ang_max = sec['ang_range']
        if ang_min > ang_max: # wraps around 0
            ang = np.random.uniform(ang_min, ang_min + 45) % 360
        else:
            ang = np.random.uniform(ang_min, ang_max)
            
        if r == 6:
            dist = np.random.uniform(76, 92)
        elif r == 4:
            dist = np.random.uniform(66, 75)
        elif r in [2, 3]:
            dist = np.random.uniform(38, 55)
        else: # 1 run
            dist = np.random.uniform(18, 35)
            
        sector_shots[s_name].append({'runs': r, 'angle': ang, 'dist': dist})
        
    summary = []
    for s in SECTORS_RHB:
        sn = s['name']
        r_sum = sector_runs[sn]
        pct = (r_sum / max(1, total_runs)) * 100.0
        summary.append({
            'sector': sn,
            'runs': r_sum,
            'pct': round(pct, 1),
            'fours': sector_fours[sn],
            'sixes': sector_sixes[sn]
        })
        
    summary_df = pd.DataFrame(summary).sort_values('runs', ascending=False)
    return {
        'total_runs': total_runs,
        'total_balls': total_balls,
        'sr': round(total_runs * 100.0 / max(1, total_balls), 1),
        'summary': summary_df,
        'shots': sector_shots,
        'vs_bowler_type': vs_bowler_type
    }, df

res, df = get_batter_wagon_data('V Kohli', vs_bowler_type='SLA')
print(f"Kohli vs SLA: {res['total_runs']} runs off {res['total_balls']} balls (SR: {res['sr']})")
print(res['summary'])
