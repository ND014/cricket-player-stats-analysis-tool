import sys
import os
sys.path.insert(0, '.')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
import pandas as pd

from matchup_engine import (
    resolve_player_name,
    get_bowler_defensive_wagon_data,
    SECTORS_LAYOUT
)

cric_name = 'DJ Bravo'
phase = 'Death'
tournament = 'ALL'

data = get_bowler_defensive_wagon_data(cric_name, phase=phase, tournament=tournament)

fig = plt.figure(figsize=(16, 7.5), dpi=140)
fig.patch.set_facecolor('#070B14')
gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 0.95], wspace=0.15)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

ax1.set_facecolor('#070B14')
radius = 75.0
inner_radius = 27.4

# Turf rings
ring_radii = [radius, radius * 0.82, radius * 0.64, radius * 0.48, radius * 0.34]
ring_colors = ['#042F2E', '#064E3B', '#042F2E', '#064E3B', '#042F2E']
for r_val, c_val in zip(ring_radii, ring_colors):
    ax1.add_patch(plt.Circle((0, 0), r_val, color=c_val, alpha=0.40, ec='none', zorder=1))

# Rope & 30yd circle
ax1.add_patch(plt.Circle((0, 0), radius, fill=False, color='#10B981', lw=2.4, alpha=0.95, zorder=3))
ax1.add_patch(plt.Circle((0, 0), inner_radius, fill=False, ls=(0, (4, 4)), color='#38BDF8', lw=1.3, alpha=0.75, zorder=3))
ax1.text(0, inner_radius + 1.8, "30-YARD CIRCLE", ha='center', va='bottom', fontsize=6.8, color='#38BDF8', alpha=0.85, fontweight='bold')

# Pitch & stumps
pitch = patches.Rectangle((-1.6, -10.0), 3.2, 20.0, color='#D97706', alpha=0.85, ec='#FDE68A', lw=0.9, zorder=4)
ax1.add_patch(pitch)
ax1.plot([-3.2, 3.2], [7.5, 7.5], color='#F3F4F6', lw=1.2, zorder=5)
ax1.plot([-3.2, 3.2], [-7.5, -7.5], color='#F3F4F6', lw=1.2, zorder=5)
ax1.plot([-1.0, 1.0], [-8.2, -8.2], color='#EF4444', lw=3.0, zorder=6)

# Sector spokes
angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
for ang in angles_deg:
    rad = np.radians(ang)
    ax1.plot([0, radius * np.cos(rad)], [0, radius * np.sin(rad)], color='#334155', ls=':', lw=0.9, alpha=0.6, zorder=2)

# Sample shots
shots = data['shots']
sample_shots = shots if len(shots) <= 130 else list(np.random.choice(shots, size=130, replace=False))
for sh in sample_shots:
    ang = sh['angle']
    dist = sh['dist']
    r = sh['runs']
    rad = np.radians(ang)
    if r == 6:
        d_plot = min(dist, radius * 1.05)
        tx, ty = d_plot * np.cos(rad), d_plot * np.sin(rad)
        ax1.plot([0, tx], [-7.5, ty], color='#EF4444', alpha=0.85, lw=1.8, zorder=5)
        ax1.scatter([tx], [ty], marker='*', color='#EF4444', s=42, zorder=8)
    elif r == 4:
        d_plot = min(dist, radius * 0.98)
        tx, ty = d_plot * np.cos(rad), d_plot * np.sin(rad)
        ax1.plot([0, tx], [-7.5, ty], color='#F59E0B', alpha=0.75, lw=1.3, zorder=5)
        ax1.scatter([tx], [ty], color='#F59E0B', s=20, zorder=7)
    else:
        d_plot = min(dist, radius * 0.70)
        tx, ty = d_plot * np.cos(rad), d_plot * np.sin(rad)
        ax1.plot([0, tx], [-7.5, ty], color='#94A3B8', alpha=0.22, lw=0.8, zorder=4)

# ALL WICKET INDUCED MARKERS (PLOTTING EVERY SINGLE ONE)
all_wkts = data['wickets']
total_w = len(all_wkts)
print(f"Plotting ALL {total_w} wicket markers...")

# Adaptive marker size and alpha based on wicket volume
if total_w > 200:
    m_size, m_alpha, m_lw = 34, 0.82, 1.1
elif total_w > 80:
    m_size, m_alpha, m_lw = 44, 0.88, 1.3
else:
    m_size, m_alpha, m_lw = 54, 0.95, 1.5

# For bowled/LBWs and close-in dismissals, disperse naturally along crease and pitch
np.random.seed(42)
for wm in all_wkts:
    x = wm['x']
    y = wm['y']
    if 'Stumps' in wm.get('type', ''):
        # Bowled/LBW happen around the stumps & batting crease
        x = np.random.uniform(-1.8, 1.8)
        y = np.random.uniform(-10.5, -6.5)
    ax1.scatter([x], [y], marker='X', color='#10B981', s=m_size, lw=m_lw, alpha=m_alpha, zorder=10)

# Sector Badges with Runs AND Wickets
for _, s_row in data['summary'].iterrows():
    s_short = s_row['Sector']
    match_sec = next(item for item in SECTORS_LAYOUT if item['short'] == s_short)
    rad = np.radians(match_sec['mid_ang'])
    x_start = radius * 1.02 * np.cos(rad)
    y_start = radius * 1.02 * np.sin(rad)
    x_end = radius * 1.15 * np.cos(rad)
    y_end = radius * 1.15 * np.sin(rad)
    ax1.plot([x_start, x_end], [y_start, y_end], color=s_row['Color'], lw=0.9, alpha=0.7, zorder=9)
    lx = radius * 1.25 * np.cos(rad)
    ly = radius * 1.25 * np.sin(rad)
    badge_text = f"{s_short.upper()}\n{s_row['Conceded_Pct']:.1f}% | {int(s_row['RunsConceded'])}r\n⚡ {int(s_row['Wickets'])} Wkts"
    ax1.text(lx, ly, badge_text, ha='center', va='center',
             fontsize=7.2, fontweight='bold', color='#F8FAFC', zorder=12,
             bbox=dict(boxstyle='round,pad=0.32,rounding_size=0.3', facecolor='#111827', edgecolor=s_row['Color'], alpha=0.95, lw=1.2))

ax1.set_xlim(-radius * 1.55, radius * 1.55)
ax1.set_ylim(-radius * 1.55, radius * 1.55)
ax1.set_aspect('equal')
ax1.axis('off')

total_w = len(all_wkts)
title_html = f"{cric_name} [BOWLER] — DEFENSIVE RADIAL MAP [PHASE: {phase.upper()}]\n{data['total_runs_conceded']} Runs Conceded  •  {total_w} Wickets Induced (All {total_w} Plotted ✕)  •  {data['overall_econ']} Econ"
ax1.set_title(title_html, color='#F8FAFC', fontsize=11.5, fontweight='bold', pad=14)

# Panel 2: Bar chart
ax2.set_facecolor('#0F172A')
for spine in ax2.spines.values():
    spine.set_color('#1E293B')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

df_sorted = data['summary'].sort_values('Conceded_Pct', ascending=True)
y_pos = np.arange(len(df_sorted))
bar_colors = ['#10B981' if i < 2 else ('#EF4444' if i >= 6 else '#38BDF8') for i in range(len(df_sorted))]
ax2.barh(y_pos, [40.0] * len(df_sorted), color='#1E293B', alpha=0.45, height=0.62, zorder=1)
ax2.barh(y_pos, df_sorted['Conceded_Pct'], color=bar_colors, edgecolor='white', linewidth=0.5, height=0.62, zorder=2)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(df_sorted['Sector'], fontsize=9.5, fontweight='bold', color='#F1F5F9')
ax2.set_xlabel('Percentage of Total Runs Conceded (%)', fontsize=9.5, fontweight='bold', color='#94A3B8', labelpad=10)
ax2.set_title(f'CONCEDED RUNS & DEFENSIVE FORTRESS AUDIT ({total_w} TOTAL OUTS)', fontsize=11, fontweight='bold', color='#F8FAFC', pad=14, loc='left')

for i, (_, r) in enumerate(df_sorted.iterrows()):
    tag = "  [FORTRESS]" if i < 2 else ("  [LEAK]" if i >= 6 else "")
    val_str = f"{r['Conceded_Pct']:.1f}%  ({int(r['RunsConceded'])}r, {int(r['Wickets'])}w){tag}"
    ax2.text(r['Conceded_Pct'] + 0.6, i, val_str, va='center', fontsize=8.2, fontweight='bold', color='#F8FAFC', zorder=3)

ax2.set_xlim(0, 40.0)
ax2.grid(axis='x', color='#334155', linestyle=':', alpha=0.45, zorder=0)
ax2.tick_params(axis='x', colors='#94A3B8', labelsize=8.5)

custom_lines = [
    Line2D([0], [0], color='#10B981', marker='X', linestyle='None', markersize=8, label=f'Wicket Induced ({total_w} total plotted ✕)'),
    Line2D([0], [0], color='#EF4444', lw=2, marker='*', markersize=8, label='Six Conceded'),
    Line2D([0], [0], color='#F59E0B', lw=2, marker='o', markersize=6, label='Four Conceded')
]
ax2.legend(handles=custom_lines, loc='lower right', facecolor='#1E293B', edgecolor='#334155',
           labelcolor='#F8FAFC', fontsize=8.5, framealpha=0.95)

out_path = 'scratch/test_all_wickets_bravo.png'
plt.savefig(out_path, bbox_inches='tight', facecolor='#070B14')
print(f"[+] Saved test plot to {out_path}!")
