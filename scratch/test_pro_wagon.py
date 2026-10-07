import os
import sys
sys.path.insert(0, os.getcwd())

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

from scratch.test_full_wagon_compare import get_batter_wagon_data, SECTORS_LAYOUT

def test_render_pro_wagon(player_name="V Kohli", vs_bowler_type="SLA"):
    data = get_batter_wagon_data(player_name, vs_bowler_type=vs_bowler_type)
    cric_name = data['player_name']
    t_runs = data['total_runs']
    t_balls = data['total_balls']
    sr = data['overall_sr']
    scope_str = "All Bowlers" if vs_bowler_type == 'ALL' else f"vs {vs_bowler_type}"
    lhb_str = "LHB" if data['is_lhb'] else "RHB"
    
    # 2-Panel Professional Layout
    fig = plt.figure(figsize=(16, 7.5), dpi=140)
    fig.patch.set_facecolor('#070B14')
    
    # Grid specification: 1.25 width for field, 0.75 for stats card
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 0.95], wspace=0.15)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    
    # ---------------------------------------------------------
    # PANEL 1: PRO CRICKET FIELD WAGON WHEEL
    # ---------------------------------------------------------
    ax1.set_facecolor('#070B14')
    radius = 75.0
    inner_radius = 27.4
    
    # Concentric Mowing Rings
    ring_radii = [radius, radius*0.82, radius*0.64, radius*0.48, radius*0.34]
    ring_colors = ['#042F2E', '#064E3B', '#042F2E', '#064E3B', '#042F2E']
    for r_val, c_val in zip(ring_radii, ring_colors):
        turf_ring = plt.Circle((0, 0), r_val, color=c_val, alpha=0.40, ec='none', zorder=1)
        ax1.add_patch(turf_ring)
        
    # Boundary Rope
    boundary_rope = plt.Circle((0, 0), radius, fill=False, color='#10B981', lw=2.4, alpha=0.95, zorder=3)
    ax1.add_patch(boundary_rope)
    
    # 30-Yard Circle
    inner_ring = plt.Circle((0, 0), inner_radius, fill=False, ls=(0, (4, 4)), color='#38BDF8', lw=1.3, alpha=0.75, zorder=3)
    ax1.add_patch(inner_ring)
    ax1.text(0, inner_radius + 1.8, "30-YARD CIRCLE", ha='center', va='bottom', fontsize=6.8, color='#38BDF8', alpha=0.85, fontweight='bold')
    
    # Pitch strip in center
    pitch = patches.Rectangle((-1.6, -10.0), 3.2, 20.0, color='#D97706', alpha=0.85, ec='#FDE68A', lw=0.9, zorder=4)
    ax1.add_patch(pitch)
    
    # Crease lines & Stumps
    ax1.plot([-3.2, 3.2], [7.5, 7.5], color='#F3F4F6', lw=1.2, zorder=5)
    ax1.plot([-3.2, 3.2], [-7.5, -7.5], color='#F3F4F6', lw=1.2, zorder=5)
    ax1.plot([-1.0, 1.0], [-8.2, -8.2], color='#EF4444', lw=3.0, zorder=6)

    # Sector spokes & Translucent Sector Wedges
    angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    for ang in angles_deg:
        rad = np.radians(ang)
        x = radius * np.cos(rad)
        y = radius * np.sin(rad)
        ax1.plot([0, x], [0, y], color='#334155', ls=':', lw=0.9, alpha=0.6, zorder=2)
        
    # Draw shots (clamped to boundary for clean aesthetics)
    shots = data['shots']
    sample_shots = shots if len(shots) <= 130 else list(np.random.choice(shots, size=130, replace=False))
    
    for sh in sample_shots:
        ang = sh['angle']
        dist = sh['dist']
        r = sh['runs']
        rad = np.radians(ang)
        
        # Clamp distances so they stay inside boundary zone and never collide with labels
        if r == 6:
            d_plot = min(dist, radius * 1.05)
            tx = d_plot * np.cos(rad)
            ty = d_plot * np.sin(rad)
            ax1.plot([0, tx], [-7.5, ty], color='#EC4899', alpha=0.85, lw=1.8, zorder=5)
            ax1.scatter([tx], [ty], marker='*', color='#EC4899', s=42, zorder=8)
        elif r == 4:
            d_plot = min(dist, radius * 0.98)
            tx = d_plot * np.cos(rad)
            ty = d_plot * np.sin(rad)
            ax1.plot([0, tx], [-7.5, ty], color='#F59E0B', alpha=0.75, lw=1.3, zorder=5)
            ax1.scatter([tx], [ty], color='#F59E0B', s=20, zorder=7)
        else: # 1s/2s
            d_plot = min(dist, radius * 0.70)
            tx = d_plot * np.cos(rad)
            ty = d_plot * np.sin(rad)
            ax1.plot([0, tx], [-7.5, ty], color='#38BDF8', alpha=0.28, lw=0.85, zorder=4)

    # Sector Callout Badges (Positioned cleanly at radius * 1.25)
    for _, s_row in data['summary'].iterrows():
        s_short = s_row['Sector']
        match_sec = next(item for item in SECTORS_LAYOUT if item['short'] == s_short)
        mid_ang = match_sec['mid_ang']
        if data['is_lhb']:
            mid_ang = (180.0 - mid_ang) % 360.0
            
        rad = np.radians(mid_ang)
        # Callout line from boundary to label
        x_start = radius * 1.02 * np.cos(rad)
        y_start = radius * 1.02 * np.sin(rad)
        x_end = radius * 1.15 * np.cos(rad)
        y_end = radius * 1.15 * np.sin(rad)
        ax1.plot([x_start, x_end], [y_start, y_end], color=s_row['Color'], lw=0.9, alpha=0.7, zorder=9)
        
        lx = radius * 1.25 * np.cos(rad)
        ly = radius * 1.25 * np.sin(rad)
        
        badge_text = f"{s_short.upper()}\n{s_row['Run_Pct']:.1f}%  |  {int(s_row['Runs'])}r"
        ax1.text(lx, ly, badge_text, ha='center', va='center',
                 fontsize=7.5, fontweight='bold', color='#F8FAFC', zorder=12,
                 bbox=dict(boxstyle='round,pad=0.32,rounding_size=0.3', facecolor='#111827', edgecolor=s_row['Color'], alpha=0.95, lw=1.2))

    # Field Orientation Subtitle
    side_text = "← OFF SIDE (LHB)        |        LEG SIDE →" if data['is_lhb'] else "← LEG SIDE (RHB)        |        OFF SIDE →"
    ax1.text(0, -radius * 1.38, side_text, ha='center', va='center', color='#94A3B8', fontsize=8.5, fontweight='bold')
    
    ax1.set_xlim(-radius * 1.52, radius * 1.52)
    ax1.set_ylim(-radius * 1.52, radius * 1.52)
    ax1.set_aspect('equal')
    ax1.axis('off')
    
    title_html = f"{cric_name} ({lhb_str}) — WAGON WHEEL [{scope_str.upper()}]\n{t_runs} Career Runs  •  {t_balls} Balls  •  {sr} Strike Rate"
    ax1.set_title(title_html, color='#F8FAFC', fontsize=12, fontweight='bold', pad=14)

    # ---------------------------------------------------------
    # PANEL 2: SECTOR BREAKDOWN CARD
    # ---------------------------------------------------------
    ax2.set_facecolor('#0F172A')
    for spine in ax2.spines.values():
        spine.set_color('#1E293B')
        spine.set_linewidth(1.0)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    df_sorted = data['summary'].sort_values('Run_Pct', ascending=True)
    y_pos = np.arange(len(df_sorted))
    
    # 1. Background Track Bars (to show proportion against max scale)
    ax2.barh(y_pos, [35.0] * len(df_sorted), color='#1E293B', alpha=0.45, height=0.62, zorder=1)
    
    # 2. Main Metric Bars
    bars = ax2.barh(y_pos, df_sorted['Run_Pct'], color=df_sorted['Color'], edgecolor='white', linewidth=0.5, height=0.62, zorder=2)
    
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(df_sorted['Sector'], fontsize=9.5, fontweight='bold', color='#F1F5F9')
    ax2.set_xlabel('Percentage of Total Runs (%)', fontsize=9.5, fontweight='bold', color='#94A3B8', labelpad=10)
    ax2.set_title('SECTOR RUN & BOUNDARY DISTRIBUTION', fontsize=11, fontweight='bold', color='#F8FAFC', pad=14, loc='left')
    
    # Data labels inline
    for i, (_, r) in enumerate(df_sorted.iterrows()):
        val_str = f"{r['Run_Pct']:.1f}%   ({int(r['Runs'])}r  •  {int(r['Fours'])}x4, {int(r['Sixes'])}x6)"
        ax2.text(r['Run_Pct'] + 0.6, i, val_str, va='center', fontsize=8.2, fontweight='bold', color='#F8FAFC', zorder=3)
                 
    ax2.set_xlim(0, 36.0)
    ax2.grid(axis='x', color='#334155', linestyle=':', alpha=0.45, zorder=0)
    ax2.tick_params(axis='x', colors='#94A3B8', labelsize=8.5)
    
    # Bottom Legend Card
    custom_lines = [
        Line2D([0], [0], color='#EC4899', lw=2, marker='*', markersize=8, label='Six (6)'),
        Line2D([0], [0], color='#F59E0B', lw=2, marker='o', markersize=6, label='Four (4)'),
        Line2D([0], [0], color='#38BDF8', lw=1.5, label='1s / 2s')
    ]
    ax2.legend(handles=custom_lines, loc='lower right', facecolor='#1E293B', edgecolor='#334155',
               labelcolor='#F8FAFC', fontsize=8.5, framealpha=0.95)
    
    plt.tight_layout()
    plt.savefig('scratch/test_pro_wagon_rendered.png', bbox_inches='tight', facecolor='#070B14')
    print("Saved scratch/test_pro_wagon_rendered.png successfully!")

test_render_pro_wagon("V Kohli", vs_bowler_type="SLA")
