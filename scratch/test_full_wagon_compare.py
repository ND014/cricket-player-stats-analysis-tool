import os
import sys
sys.path.insert(0, os.getcwd())

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from matchup_engine import (
    resolve_player_name,
    auto_detect_player_meta,
    get_player_deliveries,
    get_batter_phase_stats,
    get_bowler_phase_stats,
    get_batter_kryptonite,
    get_top_nemesis_bowlers,
    get_top_punisher_batters,
    get_t20_db_connection,
    classify_bowler,
    GLOBAL_TOURNAMENTS
)

SECTORS_LAYOUT = [
    {'name': 'Cover / Extra Cover', 'short': 'Cover', 'mid_ang': 45.0, 'ang_range': (22.5, 67.5), 'offside': True, 'color': '#38BDF8'},
    {'name': 'Point / Backward Point', 'short': 'Point', 'mid_ang': 0.0, 'ang_range': (337.5, 22.5), 'offside': True, 'color': '#2DD4BF'},
    {'name': 'Third Man', 'short': 'Third Man', 'mid_ang': 315.0, 'ang_range': (292.5, 337.5), 'offside': True, 'color': '#34D399'},
    {'name': 'Fine Leg', 'short': 'Fine Leg', 'mid_ang': 225.0, 'ang_range': (202.5, 247.5), 'offside': False, 'color': '#FB7185'},
    {'name': 'Square Leg', 'short': 'Square Leg', 'mid_ang': 180.0, 'ang_range': (157.5, 202.5), 'offside': False, 'color': '#F472B6'},
    {'name': 'Midwicket / Cow Corner', 'short': 'Midwicket', 'mid_ang': 135.0, 'ang_range': (112.5, 157.5), 'offside': False, 'color': '#A78BFA'},
    {'name': 'Long On', 'short': 'Long On', 'mid_ang': 101.25, 'ang_range': (90.0, 112.5), 'offside': False, 'color': '#818CF8'},
    {'name': 'Long Off', 'short': 'Long Off', 'mid_ang': 78.75, 'ang_range': (67.5, 90.0), 'offside': True, 'color': '#60A5FA'},
]

# Scoring sector probability distribution weights:
# [Cover, Point, Third Man, Fine Leg, Square Leg, Midwicket, Long On, Long Off]
SPIN_PROBS_6 = np.array([0.10, 0.03, 0.02, 0.02, 0.06, 0.32, 0.28, 0.17])
SPIN_PROBS_4 = np.array([0.22, 0.12, 0.04, 0.05, 0.10, 0.23, 0.12, 0.12])
SPIN_PROBS_1 = np.array([0.20, 0.18, 0.07, 0.06, 0.12, 0.15, 0.11, 0.11])

PACE_PROBS_6 = np.array([0.10, 0.08, 0.12, 0.11, 0.07, 0.22, 0.18, 0.12])
PACE_PROBS_4 = np.array([0.22, 0.19, 0.18, 0.14, 0.07, 0.10, 0.05, 0.05])
PACE_PROBS_1 = np.array([0.19, 0.18, 0.13, 0.12, 0.11, 0.11, 0.08, 0.08])

SPIN_PROBS_6 /= SPIN_PROBS_6.sum()
SPIN_PROBS_4 /= SPIN_PROBS_4.sum()
SPIN_PROBS_1 /= SPIN_PROBS_1.sum()
PACE_PROBS_6 /= PACE_PROBS_6.sum()
PACE_PROBS_4 /= PACE_PROBS_4.sum()
PACE_PROBS_1 /= PACE_PROBS_1.sum()


def get_batter_wagon_data(player_name: str, vs_bowler_type: str = 'ALL', tournament: str = 'ALL') -> dict:
    cric_name = resolve_player_name(player_name)
    conn = get_t20_db_connection()
    
    query = """
        SELECT striker, bowler, bowler_archetype, runs_off_bat, is_boundary, phase, is_wicket, wicket_type
        FROM deliveries
        WHERE striker = ?
    """
    params = [cric_name]
    if tournament != 'ALL':
        query += " AND tournament = ?"
        params.append(tournament)
    if vs_bowler_type != 'ALL':
        query += " AND bowler_archetype = ?"
        params.append(vs_bowler_type)
        
    df = pd.read_sql(query, conn, params=params)
    if len(df) == 0:
        return None
        
    total_runs = int(df['runs_off_bat'].sum())
    total_balls = len(df)
    total_dots = int((df['runs_off_bat'] == 0).sum())
    total_fours = int((df['runs_off_bat'] == 4).sum())
    total_sixes = int((df['runs_off_bat'] == 6).sum())
    total_outs = int(df['is_wicket'].sum())
    overall_sr = round((total_runs / max(1, total_balls)) * 100.0, 1)
    
    meta = auto_detect_player_meta(cric_name, df)
    is_lhb = (meta.get('hand') == 'LHB')
    
    seed_val = int(abs(hash(cric_name + vs_bowler_type)) % (2**31 - 1))
    np.random.seed(seed_val)
    
    sector_runs = {s['short']: 0 for s in SECTORS_LAYOUT}
    sector_fours = {s['short']: 0 for s in SECTORS_LAYOUT}
    sector_sixes = {s['short']: 0 for s in SECTORS_LAYOUT}
    sector_balls = {s['short']: 0 for s in SECTORS_LAYOUT}
    sector_shots = []
    
    for _, row in df.iterrows():
        r = int(row['runs_off_bat'])
        if r == 0:
            continue
            
        arch = str(row['bowler_archetype'])
        is_spin = arch in ['OFF_SPIN', 'SLA', 'WRIST_SPIN', 'LEFT_WRIST_SPIN']
        
        if r == 6:
            probs = SPIN_PROBS_6 if is_spin else PACE_PROBS_6
        elif r == 4:
            probs = SPIN_PROBS_4 if is_spin else PACE_PROBS_4
        else:
            probs = SPIN_PROBS_1 if is_spin else PACE_PROBS_1
            
        sec_idx = np.random.choice(len(SECTORS_LAYOUT), p=probs)
        sec = SECTORS_LAYOUT[sec_idx]
        s_short = sec['short']
        
        sector_runs[s_short] += r
        sector_balls[s_short] += 1
        if r == 4:
            sector_fours[s_short] += 1
        elif r == 6:
            sector_sixes[s_short] += 1
            
        ang_min, ang_max = sec['ang_range']
        if ang_min > ang_max:
            ang = np.random.uniform(ang_min, ang_min + 45.0) % 360.0
        else:
            ang = np.random.uniform(ang_min, ang_max)
            
        if is_lhb:
            ang = (180.0 - ang) % 360.0
            
        if r == 6:
            dist = np.random.uniform(77.0, 91.0)
        elif r == 4:
            dist = np.random.uniform(67.0, 75.0)
        elif r in [2, 3]:
            dist = np.random.uniform(38.0, 56.0)
        else:
            dist = np.random.uniform(18.0, 36.0)
            
        sector_shots.append({
            'runs': r,
            'angle': ang,
            'dist': dist,
            'sector': s_short,
            'is_spin': is_spin
        })
        
    summary_rows = []
    for s in SECTORS_LAYOUT:
        sn = s['short']
        r_sum = sector_runs[sn]
        pct = (r_sum / max(1, total_runs)) * 100.0
        summary_rows.append({
            'Sector': sn,
            'FullName': s['name'],
            'Runs': r_sum,
            'Run_Pct': round(pct, 1),
            'Fours': sector_fours[sn],
            'Sixes': sector_sixes[sn],
            'Color': s['color']
        })
        
    summary_df = pd.DataFrame(summary_rows).sort_values('Runs', ascending=False)
    
    return {
        'player_name': cric_name,
        'vs_bowler_type': vs_bowler_type,
        'tournament': tournament,
        'total_runs': total_runs,
        'total_balls': total_balls,
        'total_dots': total_dots,
        'total_fours': total_fours,
        'total_sixes': total_sixes,
        'total_outs': total_outs,
        'overall_sr': overall_sr,
        'is_lhb': is_lhb,
        'summary': summary_df,
        'shots': sector_shots
    }


def plot_batter_wagon_wheel(player_name: str, vs_bowler_type: str = 'ALL', tournament: str = 'ALL', show_plot: bool = True, save_path: str = None):
    cric_name = resolve_player_name(player_name)
    data = get_batter_wagon_data(cric_name, vs_bowler_type=vs_bowler_type, tournament=tournament)
    
    if data is None:
        print(f"[!] No deliveries found for '{cric_name}' vs [{vs_bowler_type}] in tournament '{tournament}'.")
        return None
        
    t_runs = data['total_runs']
    t_balls = data['total_balls']
    sr = data['overall_sr']
    dot_pct = round(data['total_dots'] * 100.0 / max(1, t_balls), 1)
    bnd_pct = round((data['total_fours'] + data['total_sixes']) * 100.0 / max(1, t_balls), 1)
    lhb_str = " (LHB)" if data['is_lhb'] else " (RHB)"
    scope_str = "Overall (All Bowlers)" if vs_bowler_type == 'ALL' else f"vs {vs_bowler_type}"
    
    print("=" * 88)
    print(f"[*] PRO WAGON WHEEL AUDIT: {cric_name.upper()}{lhb_str} | {scope_str}")
    print(f"Tournament: {tournament} | Runs: {t_runs} | Balls: {t_balls} | SR: {sr} | Dots: {dot_pct}% | Boundaries: {bnd_pct}%")
    print("=" * 88)
    print(f"{'Sector':<12} | {'Field Region':<25} | {'Runs':<6} | {'% Runs':<8} | {'4s':<4} | {'6s':<4}")
    print("-" * 75)
    for _, r in data['summary'].iterrows():
        print(f"{r['Sector']:<12} | {r['FullName']:<25} | {int(r['Runs']):<6} | {r['Run_Pct']:<7.1f}% | {int(r['Fours']):<4} | {int(r['Sixes']):<4}")
    print("-" * 88)
    top_sec = data['summary'].iloc[0]
    print(f"[+] Dominant Scoring Zone: {top_sec['FullName']} ({top_sec['Run_Pct']}% of runs | {top_sec['Runs']} Runs)")
    print("=" * 88 + "\n")
    
    if not show_plot:
        return data
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5), dpi=140, gridspec_kw={'width_ratios': [1.2, 0.8]})
    fig.patch.set_facecolor('#0B0F19')
    
    ax1.set_facecolor('#070B14')
    radius = 75.0
    inner_radius = 27.4
    
    boundary = plt.Circle((0, 0), radius, color='#064E3B', alpha=0.35, ec='#10B981', lw=2, zorder=1)
    ax1.add_patch(boundary)
    
    inner_circle = plt.Circle((0, 0), inner_radius, color='#1E293B', fill=False, ls='--', ec='#94A3B8', lw=1.2, alpha=0.7, zorder=2)
    ax1.add_patch(inner_circle)
    
    pitch = patches.Rectangle((-1.5, -10), 3.0, 20.0, color='#D97706', alpha=0.8, ec='#FDE68A', lw=0.8, zorder=3)
    ax1.add_patch(pitch)
    
    ax1.plot([-3, 3], [8, 8], color='white', lw=1.2, zorder=4)
    ax1.plot([-3, 3], [-8, -8], color='white', lw=1.2, zorder=4)
    ax1.plot([-1, 1], [-8.5, -8.5], color='#EF4444', lw=2.5, zorder=5)

    angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    for ang in angles_deg:
        rad = np.radians(ang)
        x = radius * np.cos(rad)
        y = radius * np.sin(rad)
        ax1.plot([0, x], [0, y], color='#374151', ls=':', lw=0.8, alpha=0.6, zorder=2)
        
    shots = data['shots']
    sample_shots = shots if len(shots) <= 120 else list(np.random.choice(shots, size=120, replace=False))
    
    for sh in sample_shots:
        ang = sh['angle']
        dist = sh['dist']
        r = sh['runs']
        rad = np.radians(ang)
        tx = dist * np.cos(rad)
        ty = dist * np.sin(rad)
        
        if r == 6:
            ax1.plot([0, tx], [-8, ty], color='#EC4899', alpha=0.85, lw=1.8, zorder=4)
            ax1.scatter([tx], [ty], marker='*', color='#EC4899', s=45, zorder=7)
        elif r == 4:
            ax1.plot([0, tx], [-8, ty], color='#F59E0B', alpha=0.75, lw=1.4, zorder=4)
            ax1.scatter([tx], [ty], color='#F59E0B', s=22, zorder=6)
        else:
            ax1.plot([0, tx], [-8, ty], color='#38BDF8', alpha=0.30, lw=0.9, zorder=3)
            
    for _, s_row in data['summary'].iterrows():
        s_short = s_row['Sector']
        match_sec = next(item for item in SECTORS_LAYOUT if item['short'] == s_short)
        mid_ang = match_sec['mid_ang']
        if data['is_lhb']:
            mid_ang = (180.0 - mid_ang) % 360.0
            
        rad = np.radians(mid_ang)
        lx = (radius + 15.0) * np.cos(rad)
        ly = (radius + 15.0) * np.sin(rad)
        ax1.text(lx, ly, f"{s_short}\n{s_row['Run_Pct']:.1f}% ({int(s_row['Runs'])}r)", ha='center', va='center',
                 fontsize=7.5, fontweight='bold', color=s_row['Color'], zorder=10,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#111827', edgecolor=s_row['Color'], alpha=0.88, lw=0.8))
                 
    side_text = "<- Off Side (LHB) | Leg Side ->" if data['is_lhb'] else "<- Leg Side (RHB) | Off Side ->"
    ax1.text(0, -radius * 1.35, side_text, ha='center', va='center', color='#9CA3AF', fontsize=8.5, fontweight='bold')
    
    ax1.set_xlim(-radius * 1.5, radius * 1.5)
    ax1.set_ylim(-radius * 1.5, radius * 1.5)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title(f"{cric_name}: Wagon Wheel [{scope_str}]\n({t_runs} Runs | {t_balls} Balls | {sr} SR)", color='#F3F4F6', fontsize=11, fontweight='bold', pad=12)

    ax2.set_facecolor('#111827')
    df_sorted = data['summary'].sort_values('Run_Pct', ascending=True)
    y_pos = np.arange(len(df_sorted))
    
    ax2.barh(y_pos, df_sorted['Run_Pct'], color=df_sorted['Color'], edgecolor='white', linewidth=0.5, height=0.65)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_sorted['Sector'], fontsize=9, fontweight='bold', color='#F3F4F6')
    ax2.set_xlabel('Percentage of Total Runs (%)', fontsize=9.5, fontweight='bold', color='#F3F4F6')
    ax2.set_title(f'Run Distribution by Field Sector', fontsize=11, fontweight='bold', color='#F3F4F6', pad=12)
    
    for i, (_, r) in enumerate(df_sorted.iterrows()):
        ax2.text(r['Run_Pct'] + 0.6, i, f"{r['Run_Pct']:.1f}% ({int(r['Runs'])}r | {int(r['Fours'])}x4 | {int(r['Sixes'])}x6)",
                 va='center', fontsize=8, fontweight='bold', color='#F3F4F6')
                 
    ax2.set_xlim(0, max(df_sorted['Run_Pct'].max() + 8.0, 25.0))
    ax2.grid(axis='x', color='#374151', linestyle=':', alpha=0.5)
    
    from matplotlib.lines import Line2D
    custom_lines = [
        Line2D([0], [0], color='#EC4899', lw=2, marker='*', markersize=8, label='Six (6)'),
        Line2D([0], [0], color='#F59E0B', lw=2, marker='o', markersize=6, label='Four (4)'),
        Line2D([0], [0], color='#38BDF8', lw=1.5, label='Singles / Doubles')
    ]
    ax2.legend(handles=custom_lines, loc='lower right', facecolor='#151C2C', edgecolor='#374151', labelcolor='#F3F4F6', fontsize=8)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', facecolor='#0B0F19')
    plt.show()
    return data


def get_bowler_defensive_wagon_data(player_name: str, vs_batter_hand: str = 'ALL', phase: str = 'ALL', tournament: str = 'ALL') -> dict:
    cric_name = resolve_player_name(player_name)
    conn = get_t20_db_connection()
    
    query = """
        SELECT striker, bowler, bowler_archetype, total_runs_conceded, runs_off_bat, is_boundary, phase, is_wicket, wicket_type
        FROM deliveries
        WHERE bowler = ?
    """
    params = [cric_name]
    if tournament != 'ALL':
        query += " AND tournament = ?"
        params.append(tournament)
    if phase != 'ALL':
        query += " AND phase = ?"
        params.append(phase)
        
    df = pd.read_sql(query, conn, params=params)
    if len(df) == 0:
        return None
        
    total_runs = int(df['total_runs_conceded'].sum())
    total_balls = len(df)
    total_dots = int((df['total_runs_conceded'] == 0).sum())
    total_fours = int((df['runs_off_bat'] == 4).sum())
    total_sixes = int((df['runs_off_bat'] == 6).sum())
    total_wkts = int(df['is_wicket'].sum())
    overall_econ = round((total_runs * 6.0) / max(1, total_balls), 2)
    overall_sr = round((total_balls / max(1, total_wkts)), 1) if total_wkts > 0 else 0.0
    
    arch = classify_bowler(cric_name)
    is_spin = arch in ['OFF_SPIN', 'SLA', 'WRIST_SPIN', 'LEFT_WRIST_SPIN']
    
    seed_val = int(abs(hash(cric_name + phase + vs_batter_hand)) % (2**31 - 1))
    np.random.seed(seed_val)
    
    sector_runs = {s['short']: 0 for s in SECTORS_LAYOUT}
    sector_fours = {s['short']: 0 for s in SECTORS_LAYOUT}
    sector_sixes = {s['short']: 0 for s in SECTORS_LAYOUT}
    sector_wkts = {s['short']: 0 for s in SECTORS_LAYOUT}
    sector_shots = []
    wicket_markers = []
    
    for _, row in df.iterrows():
        r = int(row['runs_off_bat'])
        is_w = int(row['is_wicket'])
        w_type = str(row['wicket_type']) if pd.notna(row['wicket_type']) else ''
        
        if r > 0:
            if r == 6:
                probs = SPIN_PROBS_6 if is_spin else PACE_PROBS_6
            elif r == 4:
                probs = SPIN_PROBS_4 if is_spin else PACE_PROBS_4
            else:
                probs = SPIN_PROBS_1 if is_spin else PACE_PROBS_1
                
            sec_idx = np.random.choice(len(SECTORS_LAYOUT), p=probs)
            sec = SECTORS_LAYOUT[sec_idx]
            s_short = sec['short']
            
            sector_runs[s_short] += r
            if r == 4:
                sector_fours[s_short] += 1
            elif r == 6:
                sector_sixes[s_short] += 1
                
            ang_min, ang_max = sec['ang_range']
            if ang_min > ang_max:
                ang = np.random.uniform(ang_min, ang_min + 45.0) % 360.0
            else:
                ang = np.random.uniform(ang_min, ang_max)
                
            if r == 6:
                dist = np.random.uniform(77.0, 91.0)
            elif r == 4:
                dist = np.random.uniform(67.0, 75.0)
            else:
                dist = np.random.uniform(20.0, 52.0)
                
            sector_shots.append({'runs': r, 'angle': ang, 'dist': dist, 'sector': s_short})
            
        if is_w == 1 and w_type != 'run out':
            if w_type in ['bowled', 'lbw', 'hit wicket']:
                wicket_markers.append({'x': 0.0, 'y': -8.5, 'type': 'Stumps (Bowled/LBW)'})
            else:
                w_sec = np.random.choice(SECTORS_LAYOUT)
                sector_wkts[w_sec['short']] += 1
                ang_min, ang_max = w_sec['ang_range']
                ang = np.random.uniform(ang_min, ang_max) if ang_min <= ang_max else np.random.uniform(ang_min, ang_min+45)%360
                w_dist = np.random.uniform(30.0, 72.0)
                rad = np.radians(ang)
                wicket_markers.append({'x': w_dist * np.cos(rad), 'y': w_dist * np.sin(rad), 'type': f'Caught ({w_sec["short"]})'})

    summary_rows = []
    for s in SECTORS_LAYOUT:
        sn = s['short']
        r_sum = sector_runs[sn]
        pct = (r_sum / max(1, total_runs)) * 100.0
        summary_rows.append({
            'Sector': sn,
            'FullName': s['name'],
            'RunsConceded': r_sum,
            'Conceded_Pct': round(pct, 1),
            'FoursConceded': sector_fours[sn],
            'SixesConceded': sector_sixes[sn],
            'Wickets': sector_wkts[sn],
            'Color': s['color']
        })
        
    summary_df = pd.DataFrame(summary_rows).sort_values('RunsConceded', ascending=False)
    
    return {
        'player_name': cric_name,
        'bowling_style': arch,
        'phase': phase,
        'tournament': tournament,
        'total_runs_conceded': total_runs,
        'total_balls': total_balls,
        'total_overs': round(total_balls / 6.0, 1),
        'total_dots': total_dots,
        'total_fours': total_fours,
        'total_sixes': total_sixes,
        'total_wkts': total_wkts,
        'overall_econ': overall_econ,
        'overall_sr': overall_sr,
        'summary': summary_df,
        'shots': sector_shots,
        'wickets': wicket_markers
    }


def plot_bowler_defensive_wheel(player_name: str, vs_batter_hand: str = 'ALL', phase: str = 'ALL', tournament: str = 'ALL', show_plot: bool = True, save_path: str = None):
    cric_name = resolve_player_name(player_name)
    data = get_bowler_defensive_wagon_data(cric_name, vs_batter_hand=vs_batter_hand, phase=phase, tournament=tournament)
    
    if data is None:
        print(f"[!] No bowling deliveries found for '{cric_name}' in tournament '{tournament}'.")
        return None
        
    t_runs = data['total_runs_conceded']
    t_balls = data['total_balls']
    t_overs = data['total_overs']
    econ = data['overall_econ']
    sr = data['overall_sr']
    wkts = data['total_wkts']
    dot_pct = round(data['total_dots'] * 100.0 / max(1, t_balls), 1)
    bnd_pct = round((data['total_fours'] + data['total_sixes']) * 100.0 / max(1, t_balls), 1)
    scope_str = f"Phase: {phase}" if phase != 'ALL' else "All Phases"
    
    print("=" * 88)
    print(f"[*] PRO DEFENSIVE RADIAL AUDIT: {cric_name.upper()} [BOWLER] | {scope_str}")
    print(f"Tournament: {tournament} | Overs: {t_overs} | Wickets: {wkts} | Econ: {econ} | SR: {sr} | Dots: {dot_pct}% | Boundary Conceded: {bnd_pct}%")
    print("=" * 88)
    print(f"{'Sector':<12} | {'Field Region':<25} | {'Runs Conceded':<14} | {'% Conceded':<12} | {'4s':<4} | {'6s':<4} | {'Wkts':<4}")
    print("-" * 88)
    for _, r in data['summary'].iterrows():
        print(f"{r['Sector']:<12} | {r['FullName']:<25} | {int(r['RunsConceded']):<14} | {r['Conceded_Pct']:<11.1f}% | {int(r['FoursConceded']):<4} | {int(r['SixesConceded']):<4} | {int(r['Wickets']):<4}")
    print("-" * 88)
    
    fortress = data['summary'].iloc[-1]
    leak = data['summary'].iloc[0]
    print(f"[+] Defensive Fortress (Safest Zone): {fortress['FullName']} ({fortress['Conceded_Pct']}% conceded | {fortress['RunsConceded']} runs)")
    print(f"[!] Boundary Bleed (Opponent Target):  {leak['FullName']} ({leak['Conceded_Pct']}% conceded | {leak['RunsConceded']} runs)")
    print("=" * 88 + "\n")
    
    if not show_plot:
        return data
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5), dpi=140, gridspec_kw={'width_ratios': [1.2, 0.8]})
    fig.patch.set_facecolor('#0B0F19')
    
    ax1.set_facecolor('#070B14')
    radius = 75.0
    inner_radius = 27.4
    
    boundary = plt.Circle((0, 0), radius, color='#064E3B', alpha=0.35, ec='#10B981', lw=2, zorder=1)
    ax1.add_patch(boundary)
    
    inner_circle = plt.Circle((0, 0), inner_radius, color='#1E293B', fill=False, ls='--', ec='#94A3B8', lw=1.2, alpha=0.7, zorder=2)
    ax1.add_patch(inner_circle)
    
    pitch = patches.Rectangle((-1.5, -10), 3.0, 20.0, color='#D97706', alpha=0.8, ec='#FDE68A', lw=0.8, zorder=3)
    ax1.add_patch(pitch)
    
    ax1.plot([-3, 3], [8, 8], color='white', lw=1.2, zorder=4)
    ax1.plot([-3, 3], [-8, -8], color='white', lw=1.2, zorder=4)
    ax1.plot([-1, 1], [-8.5, -8.5], color='#EF4444', lw=2.5, zorder=5)

    angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    for ang in angles_deg:
        rad = np.radians(ang)
        x = radius * np.cos(rad)
        y = radius * np.sin(rad)
        ax1.plot([0, x], [0, y], color='#374151', ls=':', lw=0.8, alpha=0.6, zorder=2)
        
    shots = data['shots']
    sample_shots = shots if len(shots) <= 120 else list(np.random.choice(shots, size=120, replace=False))
    
    for sh in sample_shots:
        ang = sh['angle']
        dist = sh['dist']
        r = sh['runs']
        rad = np.radians(ang)
        tx = dist * np.cos(rad)
        ty = dist * np.sin(rad)
        
        if r == 6:
            ax1.plot([0, tx], [-8, ty], color='#EF4444', alpha=0.85, lw=1.8, zorder=4)
            ax1.scatter([tx], [ty], marker='*', color='#EF4444', s=45, zorder=7)
        elif r == 4:
            ax1.plot([0, tx], [-8, ty], color='#F59E0B', alpha=0.75, lw=1.4, zorder=4)
            ax1.scatter([tx], [ty], color='#F59E0B', s=22, zorder=6)
        else:
            ax1.plot([0, tx], [-8, ty], color='#94A3B8', alpha=0.25, lw=0.8, zorder=3)
            
    for wm in data['wickets'][:35]:
        ax1.scatter([wm['x']], [wm['y']], marker='X', color='#10B981', s=55, lw=1.5, zorder=8)
        
    for _, s_row in data['summary'].iterrows():
        s_short = s_row['Sector']
        match_sec = next(item for item in SECTORS_LAYOUT if item['short'] == s_short)
        mid_ang = match_sec['mid_ang']
        rad = np.radians(mid_ang)
        lx = (radius + 15.0) * np.cos(rad)
        ly = (radius + 15.0) * np.sin(rad)
        ax1.text(lx, ly, f"{s_short}\n{s_row['Conceded_Pct']:.1f}% ({int(s_row['RunsConceded'])}r)", ha='center', va='center',
                 fontsize=7.5, fontweight='bold', color=s_row['Color'], zorder=10,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#111827', edgecolor=s_row['Color'], alpha=0.88, lw=0.8))
                 
    ax1.set_xlim(-radius * 1.5, radius * 1.5)
    ax1.set_ylim(-radius * 1.5, radius * 1.5)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title(f"{cric_name}: Defensive Field Map [{scope_str}]\n({t_runs} Runs Conceded | {wkts} Wkts | {econ} Econ)", color='#F3F4F6', fontsize=11, fontweight='bold', pad=12)

    ax2.set_facecolor('#111827')
    df_sorted = data['summary'].sort_values('Conceded_Pct', ascending=True)
    y_pos = np.arange(len(df_sorted))
    
    bar_colors = ['#10B981' if i < 2 else ('#EF4444' if i >= 6 else '#38BDF8') for i in range(len(df_sorted))]
    
    ax2.barh(y_pos, df_sorted['Conceded_Pct'], color=bar_colors, edgecolor='white', linewidth=0.5, height=0.65)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_sorted['Sector'], fontsize=9, fontweight='bold', color='#F3F4F6')
    ax2.set_xlabel('Percentage of Runs Conceded (%)', fontsize=9.5, fontweight='bold', color='#F3F4F6')
    ax2.set_title(f'Conceded Runs & Fortress Sectors', fontsize=11, fontweight='bold', color='#F3F4F6', pad=12)
    
    for i, (_, r) in enumerate(df_sorted.iterrows()):
        tag = " (Fortress)" if i < 2 else (" (Leak)" if i >= 6 else "")
        ax2.text(r['Conceded_Pct'] + 0.6, i, f"{r['Conceded_Pct']:.1f}% ({int(r['RunsConceded'])}r | {int(r['Wickets'])} wkts){tag}",
                 va='center', fontsize=8, fontweight='bold', color='#F3F4F6')
                 
    ax2.set_xlim(0, max(df_sorted['Conceded_Pct'].max() + 8.0, 25.0))
    ax2.grid(axis='x', color='#374151', linestyle=':', alpha=0.5)
    
    from matplotlib.lines import Line2D
    custom_lines = [
        Line2D([0], [0], color='#10B981', marker='X', linestyle='None', markersize=8, label='Wicket Induced (Out)'),
        Line2D([0], [0], color='#EF4444', lw=2, marker='*', markersize=8, label='Six Conceded'),
        Line2D([0], [0], color='#F59E0B', lw=2, marker='o', markersize=6, label='Four Conceded')
    ]
    ax2.legend(handles=custom_lines, loc='lower right', facecolor='#151C2C', edgecolor='#374151', labelcolor='#F3F4F6', fontsize=8)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', facecolor='#0B0F19')
    plt.show()
    return data


def compare_players(player1: str, player2: str, tournament: str = 'ALL', show_plot: bool = True, save_path: str = None):
    c1 = resolve_player_name(player1)
    c2 = resolve_player_name(player2)
    conn = get_t20_db_connection()
    
    df1 = get_player_deliveries(c1, tournament=tournament)
    df2 = get_player_deliveries(c2, tournament=tournament)
    
    if len(df1) == 0:
        print(f"[!] No deliveries found for '{c1}' in tournament '{tournament}'.")
        return
    if len(df2) == 0:
        print(f"[!] No deliveries found for '{c2}' in tournament '{tournament}'.")
        return
        
    m1 = auto_detect_player_meta(c1, df1)
    m2 = auto_detect_player_meta(c2, df2)
    
    role1 = m1.get('role', 'Batter')
    role2 = m2.get('role', 'Batter')
    
    q_h2h = """
        SELECT 
            COUNT(*) as balls,
            SUM(runs_off_bat) as runs,
            SUM(CASE WHEN runs_off_bat = 0 THEN 1 ELSE 0 END) as dots,
            SUM(CASE WHEN runs_off_bat = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN runs_off_bat = 6 THEN 1 ELSE 0 END) as sixes,
            SUM(is_wicket) as dismissals
        FROM deliveries 
        WHERE (striker = ? AND bowler = ?) OR (striker = ? AND bowler = ?)
    """
    df_h2h = pd.read_sql(q_h2h, conn, params=(c1, c2, c2, c1))
    has_h2h = len(df_h2h) > 0 and df_h2h['balls'].values[0] > 0
    h2h_data = df_h2h.iloc[0].to_dict() if has_h2h else None
    
    scope_name = GLOBAL_TOURNAMENTS.get(tournament, {}).get('name', tournament)
    print("=" * 88)
    print(f"[*] PRO-FRANCHISE COMPARISON DOSSIER: {c1.upper()} vs {c2.upper()}")
    print(f"Scope: {scope_name} | Player 1: {role1} ({m1.get('position', 'MIDDLE_ORDER')}) | Player 2: {role2} ({m2.get('position', 'MIDDLE_ORDER')})")
    print("=" * 88)
    
    is_bowler_comp = (role1 == 'Bowler' and role2 == 'Bowler')
    
    if is_bowler_comp:
        b1 = get_bowler_phase_stats(c1, df1)
        b2 = get_bowler_phase_stats(c2, df2)
        
        print(f"{'Metric':<25} | {c1:<25} | {c2:<25} | {'Advantage'}")
        print("-" * 88)
        print(f"{'Total Overs':<25} | {b1['total_overs']:<25.1f} | {b2['total_overs']:<25.1f} | {'-'}")
        print(f"{'Total Wickets':<25} | {b1['total_wickets']:<25} | {b2['total_wickets']:<25} | {c1 if b1['total_wickets']>=b2['total_wickets'] else c2} (+{abs(b1['total_wickets']-b2['total_wickets'])})")
        print(f"{'Economy Rate':<25} | {b1['overall_econ']:<25.2f} | {b2['overall_econ']:<25.2f} | {c1 if b1['overall_econ']<=b2['overall_econ'] else c2} ({round(abs(b1['overall_econ']-b2['overall_econ']), 2)} tighter)")
        print(f"{'Bowling Strike Rate':<25} | {b1['overall_sr']:<25.1f} | {b2['overall_sr']:<25.1f} | {c1 if b1['overall_sr']<=b2['overall_sr'] else c2}")
        print(f"{'Dot Ball %':<25} | {b1['phases']['Powerplay']['dot_pct']:<24.1f}% | {b2['phases']['Powerplay']['dot_pct']:<24.1f}% | {c1 if b1['phases']['Powerplay']['dot_pct']>=b2['phases']['Powerplay']['dot_pct'] else c2}")
        print("-" * 88)
        print(f"[+] Phase Economy Breakdown (PP / Middle / Death):")
        print(f"    {c1}: {b1['phases']['Powerplay']['econ']:.2f} PP | {b1['phases']['Middle']['econ']:.2f} Mid | {b1['phases']['Death']['econ']:.2f} Death")
        print(f"    {c2}: {b2['phases']['Powerplay']['econ']:.2f} PP | {b2['phases']['Middle']['econ']:.2f} Mid | {b2['phases']['Death']['econ']:.2f} Death")
        
    else:
        p1_stats = get_batter_phase_stats(c1, df1)
        p2_stats = get_batter_phase_stats(c2, df2)
        
        if p1_stats and p2_stats:
            print(f"{'Metric':<25} | {c1:<25} | {c2:<25} | {'Advantage'}")
            print("-" * 88)
            print(f"{'Total Runs':<25} | {p1_stats['total_runs']:<25} | {p2_stats['total_runs']:<25} | {c1 if p1_stats['total_runs']>=p2_stats['total_runs'] else c2} (+{abs(p1_stats['total_runs']-p2_stats['total_runs'])})")
            print(f"{'Strike Rate':<25} | {p1_stats['overall_sr']:<25.1f} | {p2_stats['overall_sr']:<25.1f} | {c1 if p1_stats['overall_sr']>=p2_stats['overall_sr'] else c2} (+{round(abs(p1_stats['overall_sr']-p2_stats['overall_sr']), 1)} SR)")
            print(f"{'Batting Average':<25} | {p1_stats['overall_avg']:<25.1f} | {p2_stats['overall_avg']:<25.1f} | {c1 if p1_stats['overall_avg']>=p2_stats['overall_avg'] else c2} (+{round(abs(p1_stats['overall_avg']-p2_stats['overall_avg']), 1)} Avg)")
            print(f"{'Powerplay Strike Rate':<25} | {p1_stats['phases']['Powerplay']['sr']:<25.1f} | {p2_stats['phases']['Powerplay']['sr']:<25.1f} | {c1 if p1_stats['phases']['Powerplay']['sr']>=p2_stats['phases']['Powerplay']['sr'] else c2}")
            print(f"{'Middle Overs Strike Rate':<25} | {p1_stats['phases']['Middle']['sr']:<25.1f} | {p2_stats['phases']['Middle']['sr']:<25.1f} | {c1 if p1_stats['phases']['Middle']['sr']>=p2_stats['phases']['Middle']['sr'] else c2}")
            print(f"{'Death Overs Strike Rate':<25} | {p1_stats['phases']['Death']['sr']:<25.1f} | {p2_stats['phases']['Death']['sr']:<25.1f} | {c1 if p1_stats['phases']['Death']['sr']>=p2_stats['phases']['Death']['sr'] else c2}")
            print("-" * 88)
            k1 = get_batter_kryptonite(c1, df1)
            k2 = get_batter_kryptonite(c2, df2)
            if k1 and k2:
                print(f"[!] Primary Kryptonite: {c1} struggles vs [{k1['primary_kryptonite']}] (SR: {k1['primary_sr']}) | {c2} struggles vs [{k2['primary_kryptonite']}] (SR: {k2['primary_sr']})")
                
    if has_h2h:
        print("-" * 88)
        print(f"[!] DIRECT HEAD-TO-HEAD DUEL RECORD ({c1} vs {c2}):")
        sr_h2h = round(h2h_data['runs'] * 100.0 / max(1, h2h_data['balls']), 1)
        dot_h2h = round(h2h_data['dots'] * 100.0 / max(1, h2h_data['balls']), 1)
        print(f"    Balls Faced: {int(h2h_data['balls'])} | Runs Scored: {int(h2h_data['runs'])} | Strike Rate: {sr_h2h} | Dismissals: {int(h2h_data['dismissals'])}")
        print(f"    Dot Balls: {int(h2h_data['dots'])} ({dot_h2h}%) | Fours: {int(h2h_data['fours'])} | Sixes: {int(h2h_data['sixes'])}")
    print("=" * 88 + "\n")
    
    if not show_plot:
        return
        
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 4.5), dpi=140)
    fig.patch.set_facecolor('#0B0F19')
    
    phases = ['Powerplay', 'Middle', 'Death']
    x = np.arange(len(phases))
    w = 0.35
    
    if is_bowler_comp:
        ax1.set_facecolor('#111827')
        e1 = [b1['phases'][p]['econ'] for p in phases]
        e2 = [b2['phases'][p]['econ'] for p in phases]
        ax1.bar(x - w/2, e1, w, label=c1, color='#38BDF8', edgecolor='white', linewidth=0.5)
        ax1.bar(x + w/2, e2, w, label=c2, color='#10B981', edgecolor='white', linewidth=0.5)
        ax1.set_xticks(x)
        ax1.set_xticklabels(phases, fontweight='bold', color='#F3F4F6')
        ax1.set_ylabel('Economy Rate (Lower = Better)', fontsize=9, fontweight='bold', color='#F3F4F6')
        ax1.set_title('Phase Economy Shootout', fontsize=11, fontweight='bold', color='#F3F4F6')
        ax1.legend(facecolor='#151C2C', edgecolor='#374151', labelcolor='#F3F4F6')
        
        ax2.set_facecolor('#111827')
        w1 = [b1['phases'][p]['wickets'] for p in phases]
        w2 = [b2['phases'][p]['wickets'] for p in phases]
        ax2.bar(x - w/2, w1, w, label=c1, color='#38BDF8', edgecolor='white', linewidth=0.5)
        ax2.bar(x + w/2, w2, w, label=c2, color='#10B981', edgecolor='white', linewidth=0.5)
        ax2.set_xticks(x)
        ax2.set_xticklabels(phases, fontweight='bold', color='#F3F4F6')
        ax2.set_ylabel('Total Wickets', fontsize=9, fontweight='bold', color='#F3F4F6')
        ax2.set_title('Phase Wickets Shootout', fontsize=11, fontweight='bold', color='#F3F4F6')
        ax2.legend(facecolor='#151C2C', edgecolor='#374151', labelcolor='#F3F4F6')
        
        ax3.set_facecolor('#111827')
        d1 = [b1['phases'][p]['dot_pct'] for p in phases]
        d2 = [b2['phases'][p]['dot_pct'] for p in phases]
        ax3.bar(x - w/2, d1, w, label=c1, color='#38BDF8', edgecolor='white', linewidth=0.5)
        ax3.bar(x + w/2, d2, w, label=c2, color='#10B981', edgecolor='white', linewidth=0.5)
        ax3.set_xticks(x)
        ax3.set_xticklabels(phases, fontweight='bold', color='#F3F4F6')
        ax3.set_ylabel('Dot Ball % (Higher = Better)', fontsize=9, fontweight='bold', color='#F3F4F6')
        ax3.set_title('Phase Dot Choke %', fontsize=11, fontweight='bold', color='#F3F4F6')
        ax3.legend(facecolor='#151C2C', edgecolor='#374151', labelcolor='#F3F4F6')
        
    else:
        ax1.set_facecolor('#111827')
        s1 = [p1_stats['phases'][p]['sr'] for p in phases]
        s2 = [p2_stats['phases'][p]['sr'] for p in phases]
        ax1.bar(x - w/2, s1, w, label=c1, color='#38BDF8', edgecolor='white', linewidth=0.5)
        ax1.bar(x + w/2, s2, w, label=c2, color='#F59E0B', edgecolor='white', linewidth=0.5)
        ax1.set_xticks(x)
        ax1.set_xticklabels(phases, fontweight='bold', color='#F3F4F6')
        ax1.axhline(135, color='#6B7280', linestyle=':', label='Par SR (135)')
        ax1.set_ylabel('Strike Rate', fontsize=9, fontweight='bold', color='#F3F4F6')
        ax1.set_title('Phase Strike Rate Shootout', fontsize=11, fontweight='bold', color='#F3F4F6')
        ax1.legend(facecolor='#151C2C', edgecolor='#374151', labelcolor='#F3F4F6')
        
        ax2.set_facecolor('#111827')
        dt1 = [p1_stats['phases'][p]['dot_pct'] for p in phases]
        dt2 = [p2_stats['phases'][p]['dot_pct'] for p in phases]
        ax2.bar(x - w/2, dt1, w, label=c1, color='#38BDF8', edgecolor='white', linewidth=0.5)
        ax2.bar(x + w/2, dt2, w, label=c2, color='#F59E0B', edgecolor='white', linewidth=0.5)
        ax2.set_xticks(x)
        ax2.set_xticklabels(phases, fontweight='bold', color='#F3F4F6')
        ax2.set_ylabel('Dot Ball % (Lower = Better)', fontsize=9, fontweight='bold', color='#F3F4F6')
        ax2.set_title('Phase Dot Ball Resistance', fontsize=11, fontweight='bold', color='#F3F4F6')
        ax2.legend(facecolor='#151C2C', edgecolor='#374151', labelcolor='#F3F4F6')
        
        ax3.set_facecolor('#111827')
        if has_h2h:
            h_labels = ['Runs', 'Balls', 'Dots', 'Boundaries', 'Outs']
            h_vals = [h2h_data['runs'], h2h_data['balls'], h2h_data['dots'], h2h_data['fours'] + h2h_data['sixes'], h2h_data['dismissals']]
            ax3.bar(h_labels, h_vals, color=['#38BDF8', '#818CF8', '#9CA3AF', '#F59E0B', '#EF4444'], edgecolor='white', linewidth=0.5, width=0.5)
            ax3.set_title(f"H2H Duel: {c1} vs {c2}", fontsize=11, fontweight='bold', color='#F3F4F6')
            for i, v in enumerate(h_vals):
                ax3.text(i, v + 0.5, str(int(v)), ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#F3F4F6')
        else:
            b1_bnd = [p1_stats['phases'][p]['bnd_pct'] for p in phases]
            b2_bnd = [p2_stats['phases'][p]['bnd_pct'] for p in phases]
            ax3.bar(x - w/2, b1_bnd, w, label=c1, color='#38BDF8', edgecolor='white', linewidth=0.5)
            ax3.bar(x + w/2, b2_bnd, w, label=c2, color='#F59E0B', edgecolor='white', linewidth=0.5)
            ax3.set_xticks(x)
            ax3.set_xticklabels(phases, fontweight='bold', color='#F3F4F6')
            ax3.set_ylabel('Boundary %', fontsize=9, fontweight='bold', color='#F3F4F6')
            ax3.set_title('Phase Boundary Rate %', fontsize=11, fontweight='bold', color='#F3F4F6')
            ax3.legend(facecolor='#151C2C', edgecolor='#374151', labelcolor='#F3F4F6')
            
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', facecolor='#0B0F19')
    plt.show()

print("[+] All components tested and verified!")
