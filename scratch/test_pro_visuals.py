import os
import sys
sys.path.insert(0, os.getcwd())

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

def draw_pro_cricket_ground(ax, radius=75.0, inner_radius=27.4):
    ax.set_facecolor('#070B14')
    
    # 1. Concentric Mowing Grass Rings (International Stadium Turf)
    ring_radii = [radius, radius*0.82, radius*0.64, radius*0.48, radius*0.34]
    ring_colors = ['#042F2E', '#064E3B', '#042F2E', '#064E3B', '#042F2E']
    for r_val, c_val in zip(ring_radii, ring_colors):
        turf_ring = plt.Circle((0, 0), r_val, color=c_val, alpha=0.45, ec='none', zorder=1)
        ax.add_patch(turf_ring)
        
    # Boundary Rope (Crisp glowing ring)
    boundary_rope = plt.Circle((0, 0), radius, fill=False, color='#10B981', lw=2.2, alpha=0.9, zorder=3)
    ax.add_patch(boundary_rope)
    
    # 30-Yard Circle (Inner fielding ring)
    inner_ring = plt.Circle((0, 0), inner_radius, fill=False, ls=(0, (4, 4)), color='#38BDF8', lw=1.3, alpha=0.75, zorder=3)
    ax.add_patch(inner_ring)
    
    # Inner 30-Yard Ring Badge
    ax.text(0, inner_radius + 1.8, "30-YARD CIRCLE", ha='center', va='bottom', fontsize=6.8,
            color='#38BDF8', alpha=0.85, fontweight='bold')
    
    # Pitch strip in center
    pitch = patches.Rectangle((-1.6, -10.0), 3.2, 20.0, color='#D97706', alpha=0.85, ec='#FDE68A', lw=0.9, zorder=4)
    ax.add_patch(pitch)
    
    # Crease lines & Stumps
    ax.plot([-3.2, 3.2], [7.5, 7.5], color='#F3F4F6', lw=1.2, zorder=5)   # Bowling crease
    ax.plot([-3.2, 3.2], [-7.5, -7.5], color='#F3F4F6', lw=1.2, zorder=5) # Batting crease
    ax.plot([-1.0, 1.0], [-8.2, -8.2], color='#EF4444', lw=3.0, zorder=6) # Stumps

    # Sector divider spokes
    angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    for ang in angles_deg:
        rad = np.radians(ang)
        x = radius * np.cos(rad)
        y = radius * np.sin(rad)
        ax.plot([0, x], [0, y], color='#334155', ls=':', lw=0.9, alpha=0.6, zorder=2)
        
    ax.set_xlim(-radius * 1.48, radius * 1.48)
    ax.set_ylim(-radius * 1.48, radius * 1.48)
    ax.set_aspect('equal')
    ax.axis('off')

fig, ax = plt.subplots(figsize=(7, 7), dpi=120)
fig.patch.set_facecolor('#0B0F19')
draw_pro_cricket_ground(ax)
plt.savefig('scratch/test_pro_ground.png', bbox_inches='tight', facecolor='#0B0F19')
print("Saved scratch/test_pro_ground.png successfully!")
