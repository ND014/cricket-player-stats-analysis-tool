import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matchup_engine import get_batter_matchup_splits, get_bowler_matchup_splits

ARCHETYPE_COLORS = {
    'LAF': '#38BDF8',            # Sky Blue
    'RAF': '#EF4444',            # Electric Red
    'LAM': '#06B6D4',            # Teal
    'RAM': '#F97316',            # Vibrant Orange
    'OFF_SPIN': '#A855F7',       # Purple
    'WRIST_SPIN': '#EC4899',     # Hot Pink
    'SLA': '#10B981',            # Emerald Green
    'LEFT_WRIST_SPIN': '#8B5CF6' # Violet
}

HAND_COLORS = {
    'RHB': '#38BDF8', # Sky Blue
    'LHB': '#F59E0B'  # Amber / Gold
}

PHASE_COLORS = {
    'Powerplay': '#38BDF8',
    'Middle': '#10B981',
    'Death': '#EF4444'
}

def plot_matchup_splits_comparison(splits_data, show_plot=False, save_path=None):
    if not splits_data:
        return None
    
    role = splits_data.get('role', 'Batter')
    cric_name = splits_data.get('cric_name', 'Player')
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.5, 4.6), dpi=140)
    fig.patch.set_facecolor('#070B14')
    
    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor('#0F172A')
        for spine in ax.spines.values():
            spine.set_color('#1E293B')
            spine.set_linewidth(1.0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', color='#334155', linestyle=':', alpha=0.45, zorder=0)

    if role == 'Batter':
        arch_list = splits_data.get('archetypes', [])
        # If no specific archetypes found
        if not arch_list:
            return None
        
        # Labels and colors
        labels = [a['archetype'] for a in arch_list]
        colors = [ARCHETYPE_COLORS.get(a['archetype'], '#38BDF8') for a in arch_list]
        x = np.arange(len(labels))
        w = 0.55 if len(labels) <= 4 else 0.65
        
        # 1. Strike Rate Comparison
        sr_vals = [a['sr'] for a in arch_list]
        bars1 = ax1.bar(x, sr_vals, width=w, color=colors, edgecolor='white', linewidth=0.5, zorder=2)
        ax1.axhline(135.0, color='#94A3B8', linestyle='--', lw=1.2, label='Par SR (135)', zorder=1)
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, fontweight='bold', color='#F1F5F9', fontsize=8.5, rotation=15 if len(labels) > 4 else 0)
        ax1.set_ylabel('Strike Rate', fontsize=9, fontweight='bold', color='#94A3B8')
        ax1.set_title('STRIKE RATE vs BOWLING STYLES', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12)
        ax1.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8, loc='upper left')
        max_sr = max(sr_vals) if sr_vals else 150
        ax1.set_ylim(0, max(160, max_sr * 1.18))
        for b in bars1:
            h = b.get_height()
            ax1.text(b.get_x() + b.get_width()/2, h + 2.5, f"{h:.1f}", ha='center', va='bottom', fontsize=8, color='#F8FAFC', fontweight='bold')

        # 2. Dot Ball Resistance % (Lower = Better)
        dots_vals = [a['dot_pct'] for a in arch_list]
        bars2 = ax2.bar(x, dots_vals, width=w, color=colors, edgecolor='white', linewidth=0.5, zorder=2)
        ax2.axhline(35.0, color='#94A3B8', linestyle='--', lw=1.2, label='T20 Par Dot % (35%)', zorder=1)
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, fontweight='bold', color='#F1F5F9', fontsize=8.5, rotation=15 if len(labels) > 4 else 0)
        ax2.set_ylabel('Dot Ball % (Lower = Better)', fontsize=9, fontweight='bold', color='#94A3B8')
        ax2.set_title('DOT BALL RESISTANCE %', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12)
        ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8, loc='upper left')
        max_dots = max(dots_vals) if dots_vals else 40
        ax2.set_ylim(0, max(50, max_dots * 1.2))
        for b in bars2:
            h = b.get_height()
            ax2.text(b.get_x() + b.get_width()/2, h + 0.8, f"{h:.1f}%", ha='center', va='bottom', fontsize=8, color='#F8FAFC', fontweight='bold')

        # 3. Batting Average & Dismissals
        avg_vals = [a['avg'] for a in arch_list]
        outs_vals = [a['dismissals'] for a in arch_list]
        bars3 = ax3.bar(x, avg_vals, width=w, color=colors, edgecolor='white', linewidth=0.5, zorder=2)
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, fontweight='bold', color='#F1F5F9', fontsize=8.5, rotation=15 if len(labels) > 4 else 0)
        ax3.set_ylabel('Batting Average (Runs / Out)', fontsize=9, fontweight='bold', color='#94A3B8')
        ax3.set_title('BATTING AVERAGE & DISMISSAL HAZARD', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12)
        max_avg = max(avg_vals) if avg_vals else 40
        ax3.set_ylim(0, max(50, max_avg * 1.2))
        for b, outs in zip(bars3, outs_vals):
            h = b.get_height()
            ax3.text(b.get_x() + b.get_width()/2, h + 1.0, f"{h:.1f}\n({outs} outs)", ha='center', va='bottom', fontsize=7.5, color='#F8FAFC', fontweight='bold')

        type_names = ', '.join(labels)
        fig.suptitle(f"TACTICAL COMPARISON: {cric_name.upper()} vs {len(labels)} BOWLING STYLES [{type_names}]",
                     fontsize=12, fontweight='bold', color='#F8FAFC', y=0.99)

    else:
        # Bowler comparison
        hands_list = splits_data.get('hands', [])
        phases_data = splits_data.get('phases', {})
        
        # Compare vs RHB and vs LHB
        labels = [f"vs {h['hand']}" for h in hands_list]
        colors = [HAND_COLORS.get(h['hand'], '#38BDF8') for h in hands_list]
        x = np.arange(len(labels))
        w = 0.45

        # 1. Economy Rate
        e_vals = [h['econ'] for h in hands_list]
        bars1 = ax1.bar(x, e_vals, width=w, color=colors, edgecolor='white', linewidth=0.5, zorder=2)
        ax1.axhline(8.0, color='#94A3B8', linestyle='--', lw=1.2, label='Par Econ (8.0)', zorder=1)
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, fontweight='bold', color='#F1F5F9', fontsize=9.5)
        ax1.set_ylabel('Economy Rate (Lower = Better)', fontsize=9, fontweight='bold', color='#94A3B8')
        ax1.set_title('ECONOMY RATE CONTAINMENT', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12)
        ax1.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8, loc='upper left')
        max_e = max(e_vals) if e_vals else 9
        ax1.set_ylim(0, max(10, max_e * 1.25))
        for b in bars1:
            h = b.get_height()
            ax1.text(b.get_x() + b.get_width()/2, h + 0.15, f"{h:.2f}", ha='center', va='bottom', fontsize=8.5, color='#F8FAFC', fontweight='bold')

        # 2. Dot Ball Choke %
        dot_vals = [h['dot_pct'] for h in hands_list]
        bars2 = ax2.bar(x, dot_vals, width=w, color=colors, edgecolor='white', linewidth=0.5, zorder=2)
        ax2.axhline(40.0, color='#94A3B8', linestyle='--', lw=1.2, label='Elite Choke (40%)', zorder=1)
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, fontweight='bold', color='#F1F5F9', fontsize=9.5)
        ax2.set_ylabel('Dot Ball % (Higher = Better)', fontsize=9, fontweight='bold', color='#94A3B8')
        ax2.set_title('DOT BALL CHOKE %', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12)
        ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8, loc='upper left')
        max_d = max(dot_vals) if dot_vals else 45
        ax2.set_ylim(0, max(50, max_d * 1.2))
        for b in bars2:
            h = b.get_height()
            ax2.text(b.get_x() + b.get_width()/2, h + 0.8, f"{h:.1f}%", ha='center', va='bottom', fontsize=8.5, color='#F8FAFC', fontweight='bold')

        # 3. Strike Rate (Balls / Wkt) & Total Wickets
        sr_vals = [h['sr'] for h in hands_list]
        wkts_vals = [h['wickets'] for h in hands_list]
        bars3 = ax3.bar(x, sr_vals, width=w, color=colors, edgecolor='white', linewidth=0.5, zorder=2)
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, fontweight='bold', color='#F1F5F9', fontsize=9.5)
        ax3.set_ylabel('Bowling SR (Balls / Wkt - Lower = Better)', fontsize=9, fontweight='bold', color='#94A3B8')
        ax3.set_title('LETHALITY & WICKETS INDUCED', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12)
        max_sr = max(sr_vals) if sr_vals else 25
        ax3.set_ylim(0, max(30, max_sr * 1.25))
        for b, wkts in zip(bars3, wkts_vals):
            h = b.get_height()
            ax3.text(b.get_x() + b.get_width()/2, h + 0.5, f"{h:.1f} SR\n({wkts} wkts)", ha='center', va='bottom', fontsize=8, color='#F8FAFC', fontweight='bold')

        fig.suptitle(f"TACTICAL COMPARISON: {cric_name.upper()} [BOWLER] — RECORD vs RHB vs LHB BATTERS",
                     fontsize=12, fontweight='bold', color='#F8FAFC', y=0.99)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', facecolor='#070B14')
    elif show_plot:
        plt.show()
    plt.close(fig)
    return fig

# Test for Kohli vs LAF, RAF, SLA, WRIST_SPIN
b_data = get_batter_matchup_splits('Virat Kohli', ['LAF', 'RAF', 'SLA', 'WRIST_SPIN'])
plot_matchup_splits_comparison(b_data, save_path='C:/Users/NITHISH/.gemini/antigravity-ide/brain/483181ff-be38-46f3-ba7a-3b897858f162/kohli_archetypes_comparison.png')
print('Saved kohli_archetypes_comparison.png')

# Test for Bumrah vs RHB, LHB
bowl_data = get_bowler_matchup_splits('Jasprit Bumrah', ['RHB', 'LHB'])
plot_matchup_splits_comparison(bowl_data, save_path='C:/Users/NITHISH/.gemini/antigravity-ide/brain/483181ff-be38-46f3-ba7a-3b897858f162/bumrah_hands_comparison.png')
print('Saved bumrah_hands_comparison.png')
