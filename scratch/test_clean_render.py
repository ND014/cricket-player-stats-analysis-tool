import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as patches

project_dir = os.path.abspath(os.getcwd())
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

import matchup_engine
from matchup_engine import get_bowler_defensive_wagon_data, SECTORS_LAYOUT

def render_clean_defensive_map(player_name='Rohit Sharma', save_path='scratch/clean_rohit_defensive.png'):
    cric_name = matchup_engine.resolve_player_name(player_name)
    data = get_bowler_defensive_wagon_data(cric_name, vs_batter_hand='ALL', phase='ALL', tournament='ALL')
    
    if data is None:
        print("No data found")
        return
        
    t_runs = data['total_runs_conceded']
    wkts = data['total_wkts']
    econ = data['overall_econ']
    
    # Setup Figure with sleek modern palette
    fig = plt.figure(figsize=(15.5, 7.2), dpi=140)
    fig.patch.set_facecolor('#0B0F19')
    
    gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 0.9], wspace=0.12)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    
    # -----------------------------------------------------------------
    # PANEL 1: CLEAN CRICKET FIELD RADIAL MAP
    # -----------------------------------------------------------------
    ax1.set_facecolor('#0B0F19')
    radius = 75.0
    inner_radius = 27.4
    
    # Clean ground surface (subtle circular turf)
    turf = plt.Circle((0, 0), radius, color='#0D1527', ec='#1E293B', lw=1.2, zorder=1)
    ax1.add_patch(turf)
    
    # Outer subtle grass glow ring
    turf_inner = plt.Circle((0, 0), radius * 0.99, color='#0F192E', ec='none', zorder=1)
    ax1.add_patch(turf_inner)
    
    # Subtle Boundary Rope
    boundary_rope = plt.Circle((0, 0), radius, fill=False, color='#10B981', lw=1.2, alpha=0.65, zorder=3)
    ax1.add_patch(boundary_rope)
    
    # 30-Yard Circle (delicate dashed line, no text clutter)
    inner_ring = plt.Circle((0, 0), inner_radius, fill=False, ls=(0, (3, 4)), color='#334155', lw=0.9, alpha=0.6, zorder=3)
    ax1.add_patch(inner_ring)
    
    # Pitch strip in center (minimalist)
    pitch = patches.Rectangle((-1.5, -9.0), 3.0, 18.0, color='#1E293B', ec='#334155', lw=0.6, alpha=0.8, zorder=4)
    ax1.add_patch(pitch)
    # Bowling crease lines
    ax1.plot([-2.6, 2.6], [7.0, 7.0], color='#64748B', lw=0.8, alpha=0.7, zorder=5)
    ax1.plot([-2.6, 2.6], [-7.0, -7.0], color='#64748B', lw=0.8, alpha=0.7, zorder=5)
    
    # Subtle Sector Dividing Spokes
    angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    for ang in angles_deg:
        rad = np.radians(ang)
        x = radius * np.cos(rad)
        y = radius * np.sin(rad)
        ax1.plot([0, x], [0, y], color='#1E293B', ls=':', lw=0.7, alpha=0.5, zorder=2)
        
    # Shot Trajectories
    shots = data['shots']
    sample_shots = shots if len(shots) <= 120 else list(np.random.choice(shots, size=120, replace=False))
    
    for sh in sample_shots:
        ang = sh['angle']
        dist = sh['dist']
        r = sh['runs']
        rad = np.radians(ang)
        
        if r == 6:
            d_plot = min(dist, radius * 1.03)
            tx = d_plot * np.cos(rad)
            ty = d_plot * np.sin(rad)
            ax1.plot([0, tx], [-7.0, ty], color='#F43F5E', alpha=0.70, lw=1.4, zorder=5)
            ax1.scatter([tx], [ty], marker='o', color='#F43F5E', s=20, zorder=7)
        elif r == 4:
            d_plot = min(dist, radius * 0.98)
            tx = d_plot * np.cos(rad)
            ty = d_plot * np.sin(rad)
            ax1.plot([0, tx], [-7.0, ty], color='#F59E0B', alpha=0.60, lw=1.1, zorder=5)
            ax1.scatter([tx], [ty], marker='o', color='#F59E0B', s=14, zorder=6)
        else:
            d_plot = min(dist, radius * 0.68)
            tx = d_plot * np.cos(rad)
            ty = d_plot * np.sin(rad)
            ax1.plot([0, tx], [-7.0, ty], color='#60A5FA', alpha=0.15, lw=0.75, zorder=4)
            
    # Wickets Induced
    all_wkts = data['wickets']
    total_w = len(all_wkts)
    for wm in all_wkts:
        ax1.scatter([wm['x']], [wm['y']], marker='X', color='#10B981', s=46, lw=1.2, alpha=0.92, zorder=10)
        
    # Perimeter Sector Labels (Clean typography without boxes or stick-pin lines)
    for _, s_row in data['summary'].iterrows():
        s_short = s_row['Sector']
        match_sec = next(item for item in SECTORS_LAYOUT if item['short'] == s_short)
        mid_ang = match_sec['mid_ang']
        rad = np.radians(mid_ang)
        
        # Position label outside boundary cleanly
        lx = radius * 1.18 * np.cos(rad)
        ly = radius * 1.18 * np.sin(rad)
        
        sec_name = s_short.title()
        pct_val = f"{s_row['Conceded_Pct']:.1f}%"
        w_val = int(s_row['Wickets'])
        w_sub = f" • {w_val}w" if w_val > 0 else ""
        
        # Two-line clean label
        ax1.text(lx, ly + 1.8, sec_name, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#E2E8F0', zorder=12)
        ax1.text(lx, ly - 2.2, f"{pct_val}{w_sub}", ha='center', va='center', fontsize=7.2, color='#94A3B8', zorder=12)

    ax1.set_xlim(-radius * 1.45, radius * 1.45)
    ax1.set_ylim(-radius * 1.45, radius * 1.45)
    ax1.set_aspect('equal')
    ax1.axis('off')
    
    # Title & Subtitle for Panel 1
    ax1.text(0, radius * 1.34, f"{cric_name} — Defensive Field Distribution", ha='center', va='bottom',
             fontsize=12, fontweight='bold', color='#F8FAFC')
    ax1.text(0, radius * 1.25, f"All Phases  •  {t_runs} Runs Conceded  •  {wkts} Wickets  •  {econ} Economy Rate",
             ha='center', va='bottom', fontsize=8.8, color='#94A3B8')

    # -----------------------------------------------------------------
    # PANEL 2: SECTOR BREAKDOWN HORIZONTAL BAR CHART
    # -----------------------------------------------------------------
    ax2.set_facecolor('#111827')
    for spine in ax2.spines.values():
        spine.set_color('#1F2937')
        spine.set_linewidth(0.8)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    df_sorted = data['summary'].sort_values('Conceded_Pct', ascending=True)
    y_pos = np.arange(len(df_sorted))
    
    # Sophisticated tonal palette based on concession rate
    # Green = low concession (protective), Slate = mid, Coral/Rose = high concession (leak)
    colors = []
    n = len(df_sorted)
    for i in range(n):
        if i < 2:
            colors.append('#10B981') # Strongest restriction
        elif i >= n - 2:
            colors.append('#F43F5E') # Highest concession
        else:
            colors.append('#3B82F6') # Balanced mid
            
    bars = ax2.barh(y_pos, df_sorted['Conceded_Pct'], color=colors, height=0.55, zorder=2)
    
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_sorted['Sector'], fontsize=9, fontweight='medium', color='#F1F5F9')
    ax2.set_xlabel('Percentage of Total Runs Conceded (%)', fontsize=8.5, color='#94A3B8', labelpad=8)
    ax2.set_title('Runs Conceded by Field Sector', fontsize=11, fontweight='bold', color='#F8FAFC', pad=14, loc='left')
    
    # Clean data labels at the end of each bar
    for i, (_, r) in enumerate(df_sorted.iterrows()):
        runs_txt = f"{int(r['RunsConceded'])} runs"
        wkts_txt = f", {int(r['Wickets'])}w" if int(r['Wickets']) > 0 else ""
        label_str = f" {r['Conceded_Pct']:.1f}%  ({runs_txt}{wkts_txt})"
        ax2.text(r['Conceded_Pct'] + 0.5, i, label_str, va='center', fontsize=8, color='#E2E8F0', fontweight='medium', zorder=3)
        
    max_pct = df_sorted['Conceded_Pct'].max()
    ax2.set_xlim(0, max(35.0, max_pct * 1.35))
    ax2.grid(axis='x', color='#1F2937', linestyle=':', alpha=0.6, zorder=0)
    ax2.tick_params(axis='x', colors='#94A3B8', labelsize=8)
    ax2.tick_params(axis='y', length=0)
    
    # Clean minimal legend
    legend_elements = [
        Line2D([0], [0], color='#10B981', marker='X', linestyle='None', markersize=7, label=f'Wickets Induced ({total_w})'),
        Line2D([0], [0], color='#F43F5E', marker='o', linestyle='None', markersize=6, label='Six Conceded'),
        Line2D([0], [0], color='#F59E0B', marker='o', linestyle='None', markersize=5, label='Four Conceded')
    ]
    ax2.legend(handles=legend_elements, loc='lower right', facecolor='#1F2937', edgecolor='#374151',
               labelcolor='#D1D5DB', fontsize=8, framealpha=0.9)
               
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', facecolor='#0B0F19')
    plt.close()
    print(f"Saved clean defensive visual to {save_path}")

def render_clean_batter_wagon(player_name='Virat Kohli', vs_bowler_type='ALL', save_path='scratch/clean_kohli_wagon.png'):
    cric_name = matchup_engine.resolve_player_name(player_name)
    display_name = matchup_engine.get_player_display_name(cric_name)
    data = matchup_engine.get_batter_wagon_data(cric_name, vs_bowler_type=vs_bowler_type, tournament='ALL')
    
    if data is None:
        print("No batter data found")
        return
        
    t_runs = data['total_runs']
    t_balls = data['total_balls']
    sr = data['overall_sr']
    dot_pct = round(data['total_dots'] * 100.0 / max(1, t_balls), 1)
    bnd_pct = round((data['total_fours'] + data['total_sixes']) * 100.0 / max(1, t_balls), 1)
    stance = "LHB" if data['is_lhb'] else "RHB"
    scope_str = "All Bowlers" if vs_bowler_type == 'ALL' else f"vs {vs_bowler_type}"
    
    fig = plt.figure(figsize=(15.5, 7.2), dpi=140)
    fig.patch.set_facecolor('#0B0F19')
    
    gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 0.9], wspace=0.12)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    
    # PANEL 1: WAGON WHEEL RADIAL
    ax1.set_facecolor('#0B0F19')
    radius = 75.0
    inner_radius = 27.4
    
    turf = plt.Circle((0, 0), radius, color='#0D1527', ec='#1E293B', lw=1.2, zorder=1)
    ax1.add_patch(turf)
    
    boundary_rope = plt.Circle((0, 0), radius, fill=False, color='#10B981', lw=1.2, alpha=0.65, zorder=3)
    ax1.add_patch(boundary_rope)
    
    inner_ring = plt.Circle((0, 0), inner_radius, fill=False, ls=(0, (3, 4)), color='#334155', lw=0.9, alpha=0.6, zorder=3)
    ax1.add_patch(inner_ring)
    
    pitch = patches.Rectangle((-1.5, -9.0), 3.0, 18.0, color='#1E293B', ec='#334155', lw=0.6, alpha=0.8, zorder=4)
    ax1.add_patch(pitch)
    ax1.plot([-2.6, 2.6], [7.0, 7.0], color='#64748B', lw=0.8, alpha=0.7, zorder=5)
    ax1.plot([-2.6, 2.6], [-7.0, -7.0], color='#64748B', lw=0.8, alpha=0.7, zorder=5)
    
    angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    for ang in angles_deg:
        rad = np.radians(ang)
        x = radius * np.cos(rad)
        y = radius * np.sin(rad)
        ax1.plot([0, x], [0, y], color='#1E293B', ls=':', lw=0.7, alpha=0.5, zorder=2)
        
    shots = data['shots']
    sample_shots = shots if len(shots) <= 120 else list(np.random.choice(shots, size=120, replace=False))
    
    for sh in sample_shots:
        ang = sh['angle']
        dist = sh['dist']
        r = sh['runs']
        rad = np.radians(ang)
        
        if r == 6:
            d_plot = min(dist, radius * 1.03)
            tx = d_plot * np.cos(rad)
            ty = d_plot * np.sin(rad)
            ax1.plot([0, tx], [-7.0, ty], color='#F43F5E', alpha=0.75, lw=1.5, zorder=5)
            ax1.scatter([tx], [ty], marker='o', color='#F43F5E', s=22, zorder=7)
        elif r == 4:
            d_plot = min(dist, radius * 0.98)
            tx = d_plot * np.cos(rad)
            ty = d_plot * np.sin(rad)
            ax1.plot([0, tx], [-7.0, ty], color='#F59E0B', alpha=0.65, lw=1.2, zorder=5)
            ax1.scatter([tx], [ty], marker='o', color='#F59E0B', s=16, zorder=6)
        else:
            d_plot = min(dist, radius * 0.68)
            tx = d_plot * np.cos(rad)
            ty = d_plot * np.sin(rad)
            ax1.plot([0, tx], [-7.0, ty], color='#38BDF8', alpha=0.18, lw=0.75, zorder=4)
            
    # Perimeter Sector Labels
    for _, s_row in data['summary'].iterrows():
        s_short = s_row['Sector']
        match_sec = next(item for item in SECTORS_LAYOUT if item['short'] == s_short)
        mid_ang = match_sec['mid_ang']
        if data['is_lhb']:
            mid_ang = (180.0 - mid_ang) % 360.0
        rad = np.radians(mid_ang)
        
        lx = radius * 1.18 * np.cos(rad)
        ly = radius * 1.18 * np.sin(rad)
        
        sec_name = s_short.title()
        pct_val = f"{s_row['Run_Pct']:.1f}%"
        runs_val = f"{int(s_row['Runs'])}r"
        
        ax1.text(lx, ly + 1.8, sec_name, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#E2E8F0', zorder=12)
        ax1.text(lx, ly - 2.2, f"{pct_val} • {runs_val}", ha='center', va='center', fontsize=7.2, color='#94A3B8', zorder=12)

    side_note = "← Off Side        |        Leg Side →" if not data['is_lhb'] else "← Leg Side        |        Off Side →"
    ax1.text(0, -radius * 1.25, side_note, ha='center', va='center', color='#64748B', fontsize=7.8)

    ax1.set_xlim(-radius * 1.48, radius * 1.48)
    ax1.set_ylim(-radius * 1.48, radius * 1.48)
    ax1.set_aspect('equal')
    ax1.axis('off')
    
    ax1.text(0, radius * 1.34, f"{display_name} ({stance}) — Wagon Wheel", ha='center', va='bottom',
             fontsize=12, fontweight='bold', color='#F8FAFC')
    ax1.text(0, radius * 1.25, f"{scope_str}  •  {t_runs:,} Runs ({t_balls:,}b)  •  {sr:.1f} SR  •  {bnd_pct}% Boundaries",
             ha='center', va='bottom', fontsize=8.8, color='#94A3B8')

    # PANEL 2: RUN DISTRIBUTION BY SECTOR
    ax2.set_facecolor('#111827')
    for spine in ax2.spines.values():
        spine.set_color('#1F2937')
        spine.set_linewidth(0.8)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    df_sorted = data['summary'].sort_values('Run_Pct', ascending=True)
    y_pos = np.arange(len(df_sorted))
    
    # Palette: Gradient from subtle slate-blue to vibrant cyan for dominant scoring zones
    n = len(df_sorted)
    colors = []
    for i in range(n):
        if i >= n - 2:
            colors.append('#38BDF8') # Primary scoring sectors
        elif i >= n - 4:
            colors.append('#60A5FA') # Secondary scoring sectors
        else:
            colors.append('#64748B') # Lower volume sectors
            
    bars = ax2.barh(y_pos, df_sorted['Run_Pct'], color=colors, height=0.55, zorder=2)
    
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_sorted['Sector'], fontsize=9, fontweight='medium', color='#F1F5F9')
    ax2.set_xlabel('Percentage of Total Runs Scored (%)', fontsize=8.5, color='#94A3B8', labelpad=8)
    ax2.set_title('Run Scoring Distribution by Sector', fontsize=11, fontweight='bold', color='#F8FAFC', pad=14, loc='left')
    
    for i, (_, r) in enumerate(df_sorted.iterrows()):
        fours_txt = f"{int(r['Fours'])}x4"
        sixes_txt = f", {int(r['Sixes'])}x6" if int(r['Sixes']) > 0 else ""
        label_str = f" {r['Run_Pct']:.1f}%  ({int(r['Runs'])} runs • {fours_txt}{sixes_txt})"
        ax2.text(r['Run_Pct'] + 0.5, i, label_str, va='center', fontsize=8, color='#E2E8F0', fontweight='medium', zorder=3)
        
    max_pct = df_sorted['Run_Pct'].max()
    ax2.set_xlim(0, max(32.0, max_pct * 1.35))
    ax2.grid(axis='x', color='#1F2937', linestyle=':', alpha=0.6, zorder=0)
    ax2.tick_params(axis='x', colors='#94A3B8', labelsize=8)
    ax2.tick_params(axis='y', length=0)
    
    legend_elements = [
        Line2D([0], [0], color='#F43F5E', marker='o', linestyle='None', markersize=6, label='Six (6)'),
        Line2D([0], [0], color='#F59E0B', marker='o', linestyle='None', markersize=5, label='Four (4)'),
        Line2D([0], [0], color='#38BDF8', lw=1.2, label='1s / 2s / 3s')
    ]
    ax2.legend(handles=legend_elements, loc='lower right', facecolor='#1F2937', edgecolor='#374151',
               labelcolor='#D1D5DB', fontsize=8, framealpha=0.9)
               
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', facecolor='#0B0F19')
    plt.close()
    print(f"Saved clean batter visual to {save_path}")

def render_clean_splits(player_name='Virat Kohli', save_path='scratch/clean_splits.png'):
    cric_name = matchup_engine.resolve_player_name(player_name)
    display_name = matchup_engine.get_player_display_name(cric_name)
    splits_data = matchup_engine.get_batter_matchup_splits(cric_name)
    
    if not splits_data:
        print("No splits data found")
        return
        
    arch_colors = {
        'LAF': '#F43F5E', 'RAF': '#E11D48', 'LAM': '#0284C7', 'RAM': '#F59E0B',
        'OFF_SPIN': '#6366F1', 'WRIST_SPIN': '#8B5CF6', 'SLA': '#10B981', 'LEFT_WRIST_SPIN': '#A855F7'
    }
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.5, 4.8), dpi=140)
    fig.patch.set_facecolor('#0B0F19')
    
    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor('#111827')
        for spine in ax.spines.values():
            spine.set_color('#1F2937')
            spine.set_linewidth(0.8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', color='#1F2937', linestyle=':', alpha=0.6, zorder=0)
        ax.tick_params(axis='x', colors='#D1D5DB', labelsize=8.5)
        ax.tick_params(axis='y', colors='#94A3B8', labelsize=8)
        
    arch_list = splits_data.get('archetypes', [])
    labels = [a['archetype'] for a in arch_list]
    colors = [arch_colors.get(a['archetype'], '#38BDF8') for a in arch_list]
    x = np.arange(len(labels))
    w = 0.52
    
    # 1. Strike Rate
    sr_vals = [a['sr'] for a in arch_list]
    bars1 = ax1.bar(x, sr_vals, width=w, color=colors, zorder=2)
    ax1.axhline(135.0, color='#64748B', linestyle='--', lw=1.0, zorder=1)
    ax1.text(len(labels) - 0.5, 137.0, 'Par (135)', color='#94A3B8', fontsize=7.5, ha='right', va='bottom')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, color='#F1F5F9', fontsize=8, rotation=18 if len(labels) > 4 else 0)
    ax1.set_ylabel('Strike Rate', fontsize=8.5, color='#94A3B8', labelpad=6)
    ax1.set_title('Strike Rate vs Bowling Styles', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
    ax1.set_ylim(0, max(160, max(sr_vals) * 1.18))
    for b in bars1:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width()/2, h + 2.0, f"{h:.1f}", ha='center', va='bottom', fontsize=7.8, color='#E2E8F0', fontweight='bold')

    # 2. Dot Ball %
    dots_vals = [a['dot_pct'] for a in arch_list]
    bars2 = ax2.bar(x, dots_vals, width=w, color=colors, zorder=2)
    ax2.axhline(35.0, color='#64748B', linestyle='--', lw=1.0, zorder=1)
    ax2.text(len(labels) - 0.5, 36.0, 'Par (35%)', color='#94A3B8', fontsize=7.5, ha='right', va='bottom')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, color='#F1F5F9', fontsize=8, rotation=18 if len(labels) > 4 else 0)
    ax2.set_ylabel('Dot Ball % (Lower = Better)', fontsize=8.5, color='#94A3B8', labelpad=6)
    ax2.set_title('Dot Ball Percentage', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
    ax2.set_ylim(0, max(50, max(dots_vals) * 1.2))
    for b in bars2:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width()/2, h + 0.8, f"{h:.1f}%", ha='center', va='bottom', fontsize=7.8, color='#E2E8F0', fontweight='bold')

    # 3. Batting Average
    avg_vals = [a['avg'] for a in arch_list]
    outs_vals = [a['dismissals'] for a in arch_list]
    bars3 = ax3.bar(x, avg_vals, width=w, color=colors, zorder=2)
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, color='#F1F5F9', fontsize=8, rotation=18 if len(labels) > 4 else 0)
    ax3.set_ylabel('Batting Average', fontsize=8.5, color='#94A3B8', labelpad=6)
    ax3.set_title('Batting Average & Dismissals', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
    ax3.set_ylim(0, max(50, max(avg_vals) * 1.25))
    for b, outs in zip(bars3, outs_vals):
        h = b.get_height()
        ax3.text(b.get_x() + b.get_width()/2, h + 1.2, f"{h:.1f}\n({outs}w)", ha='center', va='bottom', fontsize=7.5, color='#E2E8F0', fontweight='medium')

    fig.suptitle(f"{cric_name} — Performance Splits vs Bowling Styles",
                 fontsize=12, fontweight='bold', color='#F8FAFC', y=1.02)
                 
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', facecolor='#0B0F19')
    plt.close()
    print(f"Saved clean splits visual to {save_path}")

if __name__ == '__main__':
    render_clean_defensive_map()
    render_clean_batter_wagon()
    render_clean_splits()
