import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_cricket_field(ax, radius=75, inner_radius=27.4):
    ax.set_facecolor('#0B0F19')
    
    # Boundary turf (outer circle)
    boundary = plt.Circle((0, 0), radius, color='#064E3B', alpha=0.35, ec='#10B981', lw=2, zorder=1)
    ax.add_patch(boundary)
    
    # 30-yard circle (inner circle)
    inner_circle = plt.Circle((0, 0), inner_radius, color='#1E293B', fill=False, ls='--', ec='#94A3B8', lw=1.2, alpha=0.7, zorder=2)
    ax.add_patch(inner_circle)
    
    # Pitch strip in center
    pitch = patches.Rectangle((-1.5, -10), 3.0, 20.0, color='#D97706', alpha=0.8, ec='#FDE68A', lw=0.8, zorder=3)
    ax.add_patch(pitch)
    
    # Stumps & Crease markings
    ax.plot([-3, 3], [8, 8], color='white', lw=1.2, zorder=4)   # Bowling crease
    ax.plot([-3, 3], [-8, -8], color='white', lw=1.2, zorder=4) # Batting crease
    ax.plot([-1, 1], [-8.5, -8.5], color='#EF4444', lw=2.5, zorder=5) # Stumps

    # Draw 8 Sector Dividers
    angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    for ang in angles_deg:
        rad = np.radians(ang)
        x = radius * np.cos(rad)
        y = radius * np.sin(rad)
        ax.plot([0, x], [0, y], color='#374151', ls=':', lw=0.8, alpha=0.6, zorder=2)
        
    ax.set_xlim(-radius * 1.25, radius * 1.25)
    ax.set_ylim(-radius * 1.25, radius * 1.25)
    ax.set_aspect('equal')
    ax.axis('off')

fig, ax = plt.subplots(figsize=(6, 6), dpi=100)
fig.patch.set_facecolor('#0B0F19')
draw_cricket_field(ax)
plt.savefig('scratch/test_field.png', bbox_inches='tight', facecolor='#0B0F19')
print("Saved scratch/test_field.png successfully!")
