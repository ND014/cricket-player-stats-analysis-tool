import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_test_wagon_wheel():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=120, gridspec_kw={'width_ratios': [1.2, 0.8]})
    fig.patch.set_facecolor('#0B0F19')
    
    # 1. Cricket Field on Left
    ax1.set_facecolor('#070B14')
    radius = 75
    inner_radius = 27.4
    
    # Boundary turf (outer circle)
    boundary = plt.Circle((0, 0), radius, color='#064E3B', alpha=0.35, ec='#10B981', lw=2, zorder=1)
    ax1.add_patch(boundary)
    
    # 30-yard circle (inner circle)
    inner_circle = plt.Circle((0, 0), inner_radius, color='#1E293B', fill=False, ls='--', ec='#94A3B8', lw=1.2, alpha=0.7, zorder=2)
    ax1.add_patch(inner_circle)
    
    # Pitch strip in center
    pitch = patches.Rectangle((-1.5, -10), 3.0, 20.0, color='#D97706', alpha=0.8, ec='#FDE68A', lw=0.8, zorder=3)
    ax1.add_patch(pitch)
    
    # Crease lines
    ax1.plot([-3, 3], [8, 8], color='white', lw=1.2, zorder=4)   # Bowling crease
    ax1.plot([-3, 3], [-8, -8], color='white', lw=1.2, zorder=4) # Batting crease
    ax1.plot([-1, 1], [-8.5, -8.5], color='#EF4444', lw=2.5, zorder=5) # Stumps

    # Sector Dividers and Labels
    angles_deg = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    for ang in angles_deg:
        rad = np.radians(ang)
        x = radius * np.cos(rad)
        y = radius * np.sin(rad)
        ax1.plot([0, x], [0, y], color='#374151', ls=':', lw=0.8, alpha=0.6, zorder=2)
        
    # Sample sector data
    sectors = [
        ('Cover', 45, '19.8% (159r)', '#38BDF8'),
        ('Long Off', 78.75, '9.0% (72r)', '#60A5FA'),
        ('Long On', 101.25, '12.6% (101r)', '#818CF8'),
        ('Midwicket', 135, '16.5% (132r)', '#A78BFA'),
        ('Square Leg', 180, '6.7% (54r)', '#F472B6'),
        ('Fine Leg', 225, '7.6% (61r)', '#FB7185'),
        ('Third Man', 315, '14.1% (113r)', '#34D399'),
        ('Point', 0, '13.7% (110r)', '#2DD4BF'),
    ]
    
    for name, mid_ang, label, col in sectors:
        rad = np.radians(mid_ang)
        lx = (radius + 14) * np.cos(rad)
        ly = (radius + 14) * np.sin(rad)
        ax1.text(lx, ly, f"{name}\n{label}", ha='center', va='center', fontsize=8, fontweight='bold', color=col,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#111827', edgecolor=col, alpha=0.85, lw=0.8))
        
    # Draw simulated shot lines
    np.random.seed(42)
    for _ in range(35): # 1s/2s
        ang = np.random.uniform(0, 360)
        dist = np.random.uniform(20, 50)
        rad = np.radians(ang)
        ax1.plot([0, dist*np.cos(rad)], [-8, dist*np.sin(rad)], color='#38BDF8', alpha=0.35, lw=1.0)
    for _ in range(25): # 4s
        ang = np.random.uniform(0, 360)
        dist = np.random.uniform(68, 75)
        rad = np.radians(ang)
        ax1.plot([0, dist*np.cos(rad)], [-8, dist*np.sin(rad)], color='#F59E0B', alpha=0.7, lw=1.5)
        ax1.scatter([dist*np.cos(rad)], [dist*np.sin(rad)], color='#F59E0B', s=20, zorder=6)
    for _ in range(12): # 6s
        ang = np.random.uniform(0, 360)
        dist = np.random.uniform(78, 88)
        rad = np.radians(ang)
        ax1.plot([0, dist*np.cos(rad)], [-8, dist*np.sin(rad)], color='#EC4899', alpha=0.85, lw=2.0)
        ax1.scatter([dist*np.cos(rad)], [dist*np.sin(rad)], color='#EC4899', marker='*', s=45, zorder=7)

    ax1.set_xlim(-radius * 1.45, radius * 1.45)
    ax1.set_ylim(-radius * 1.45, radius * 1.45)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title("V Kohli vs LAF: Wagon Wheel\n(584 Balls | 802 Runs | 137.3 SR)", color='#F3F4F6', fontsize=12, fontweight='bold', pad=15)
    
    # 2. Sector Leaderboard Bar Chart on Right
    ax2.set_facecolor('#111827')
    sec_names = [s[0] for s in sectors]
    sec_pcts = [19.8, 9.0, 12.6, 16.5, 6.7, 7.6, 14.1, 13.7]
    bar_cols = [s[3] for s in sectors]
    
    # Sort by percentage
    order = np.argsort(sec_pcts)
    y_pos = np.arange(len(sec_names))
    ax2.barh(y_pos, [sec_pcts[i] for i in order], color=[bar_cols[i] for i in order], edgecolor='white', linewidth=0.5, height=0.65)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([sec_names[i] for i in order], fontsize=9, fontweight='bold', color='#F3F4F6')
    ax2.set_xlabel('Percentage of Runs (%)', fontsize=10, fontweight='bold', color='#F3F4F6')
    ax2.set_title('Sector Run Distribution Breakdown', fontsize=12, fontweight='bold', color='#F3F4F6', pad=15)
    
    for i, p in enumerate([sec_pcts[idx] for idx in order]):
        ax2.text(p + 0.5, i, f"{p:.1f}%", va='center', fontsize=9, fontweight='bold', color='#F3F4F6')
        
    ax2.set_xlim(0, max(sec_pcts) + 5)
    ax2.grid(axis='x', color='#374151', linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('scratch/test_wagon_plot.png', bbox_inches='tight', facecolor='#0B0F19')
    print("Saved scratch/test_wagon_plot.png successfully!")

plot_test_wagon_wheel()
