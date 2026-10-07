import os
import sys
sys.path.insert(0, os.getcwd())

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from scratch.test_full_wagon_compare import get_bowler_defensive_wagon_data, SECTORS_LAYOUT, resolve_player_name

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
    
    # 1. Cricket Field Visualization
    ax1.set_facecolor('#070B14')
    radius = 75.0
    inner_radius = 27.4
    
    # Boundary turf
    boundary = plt.Circle((0, 0), radius, color='#064E3B', alpha=0.35, ec='#10B981', lw=2, zorder=1)
    ax1.add_patch(boundary)
    
    # 30-yard circle
    inner_circle = plt.Circle((0, 0), inner_radius, color='#1E293B', fill=False, ls='--', ec='#94A3B8', lw=1.2, alpha=0.7, zorder=2)
    ax1.add_patch(inner_circle)
    
    # Pitch strip in center
    pitch = patches.Rectangle((-1.5, -10), 3.0, 20.0, color='#D97706', alpha=0.8, ec='#FDE68A', lw=0.8, zorder=3)
    ax1.add_patch(pitch)
    
    # Crease lines & stumps
    ax1.plot([-3, 3], [8, 8], color='white', lw=1.2, zorder=4)
    ax1.plot([-3, 3], [-8, -8], color='white', lw=1.2, zorder=4)
    ax1.plot([-1, 1], [-8.5, -8.5], color='#EF4444', lw=2.5, zorder=5)

    # Sector Dividers
    angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    for ang in angles_deg:
        rad = np.radians(ang)
        x = radius * np.cos(rad)
        y = radius * np.sin(rad)
        ax1.plot([0, x], [0, y], color='#374151', ls=':', lw=0.8, alpha=0.6, zorder=2)
        
    # Draw sample conceded shot rays
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
        else: # 1s/2s
            ax1.plot([0, tx], [-8, ty], color='#94A3B8', alpha=0.25, lw=0.8, zorder=3)
            
    # Wicket markers
    for wm in data['wickets'][:35]:
        ax1.scatter([wm['x']], [wm['y']], marker='X', color='#10B981', s=55, lw=1.5, zorder=8)
        
    # Sector percentage labels
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

    # 2. Sector Leaderboard Bar Chart
    ax2.set_facecolor('#111827')
    df_sorted = data['summary'].sort_values('Conceded_Pct', ascending=True)
    y_pos = np.arange(len(df_sorted))
    
    # Color-code by vulnerability
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

print("[+] plot_bowler_defensive_wheel defined!")
plot_bowler_defensive_wheel("JJ Bumrah", phase="Death", show_plot=False)
