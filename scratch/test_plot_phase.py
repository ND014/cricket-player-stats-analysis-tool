import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from matchup_engine import get_batter_matchup_splits, get_player_full_name

def plot_matchup_phase_splits(splits_data: dict, show_plot: bool = False, save_path = None):
    if not splits_data or 'phases' not in splits_data:
        return None

    role = splits_data.get('role', 'Batter')
    cric_name = splits_data.get('cric_name', '')
    full_name = get_player_full_name(cric_name)
    phases = ['Powerplay', 'Middle', 'Death']

    phase_colors = {
        'Powerplay': '#38BDF8',
        'Middle': '#10B981',
        'Death': '#EF4444'
    }

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16.5, 4.6), dpi=140)
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

    labels = phases
    colors = [phase_colors.get(p, '#38BDF8') for p in phases]
    x = np.arange(len(phases))
    w = 0.48

    if role == 'Batter':
        arch_list = splits_data.get('archetypes', [])
        sel_types = [a['archetype'] for a in arch_list]
        if len(sel_types) == 1:
            scope_str = sel_types[0]
        elif len(sel_types) <= 3:
            scope_str = ", ".join(sel_types)
        elif len(sel_types) == 8:
            scope_str = "All Bowling Styles"
        else:
            scope_str = f"{len(sel_types)} Selected Styles ({', '.join(sel_types[:2])}...)"

        p_sr = [splits_data['phases'][p]['sr'] for p in phases]
        p_dots = [splits_data['phases'][p]['dot_pct'] for p in phases]
        p_avg = [splits_data['phases'][p]['avg'] for p in phases]
        p_outs = [splits_data['phases'][p]['dismissals'] for p in phases]

        # 1. Phase SR
        bars1 = ax1.bar(x, p_sr, width=w, color=colors, zorder=2)
        ax1.axhline(135.0, color='#64748B', linestyle='--', lw=1.0, zorder=1)
        ax1.text(len(labels) - 0.5, 137.0, 'Par (135)', color='#94A3B8', fontsize=7.5, ha='right', va='bottom')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, color='#F1F5F9', fontsize=9)
        ax1.set_ylabel('Strike Rate', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax1.set_title(f"Phase Strike Rate vs {scope_str}", fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
        ax1.set_ylim(0, max(160, max(p_sr, default=100) * 1.18))
        for b in bars1:
            h = b.get_height()
            ax1.text(b.get_x() + b.get_width()/2, h + 2.0, f"{h:.1f}", ha='center', va='bottom', fontsize=8, color='#E2E8F0', fontweight='bold')

        # 2. Phase Dot %
        bars2 = ax2.bar(x, p_dots, width=w, color=colors, zorder=2)
        ax2.axhline(35.0, color='#64748B', linestyle='--', lw=1.0, zorder=1)
        ax2.text(len(labels) - 0.5, 36.0, 'Par (35%)', color='#94A3B8', fontsize=7.5, ha='right', va='bottom')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, color='#F1F5F9', fontsize=9)
        ax2.set_ylabel('Dot Ball % (Lower = Better)', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax2.set_title(f"Phase Dot Ball % vs {scope_str}", fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
        ax2.set_ylim(0, max(50, max(p_dots, default=40) * 1.2))
        for b in bars2:
            h = b.get_height()
            ax2.text(b.get_x() + b.get_width()/2, h + 0.8, f"{h:.1f}%", ha='center', va='bottom', fontsize=8, color='#E2E8F0', fontweight='bold')

        # 3. Phase Average
        bars3 = ax3.bar(x, p_avg, width=w, color=colors, zorder=2)
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, color='#F1F5F9', fontsize=9)
        ax3.set_ylabel('Batting Average', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax3.set_title(f"Phase Average vs {scope_str}", fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
        ax3.set_ylim(0, max(50, max(p_avg, default=40) * 1.25))
        for b, outs in zip(bars3, p_outs):
            h = b.get_height()
            ax3.text(b.get_x() + b.get_width()/2, h + 1.2, f"{h:.1f}\n({outs}w)", ha='center', va='bottom', fontsize=7.5, color='#E2E8F0', fontweight='medium')

        fig.suptitle(f"{full_name} vs {scope_str} Across Phases",
                     fontsize=12, fontweight='bold', color='#F8FAFC', y=1.02)
    else:
        # Bowler Phase breakdown
        hands_list = splits_data.get('hands', [])
        sel_hands = [h['hand'] for h in hands_list]
        scope_str = "All Batters" if len(sel_hands) == 2 else f"vs {', '.join(sel_hands)}"

        p_econ = [splits_data['phases'][p]['econ'] for p in phases]
        p_dots = [splits_data['phases'][p]['dot_pct'] for p in phases]
        p_sr = [splits_data['phases'][p]['sr'] for p in phases]
        p_wkts = [splits_data['phases'][p]['wickets'] for p in phases]

        # 1. Economy Rate
        bars1 = ax1.bar(x, p_econ, width=w, color=colors, zorder=2)
        ax1.axhline(8.0, color='#64748B', linestyle='--', lw=1.0, zorder=1)
        ax1.text(len(labels) - 0.5, 8.15, 'Par (8.0)', color='#94A3B8', fontsize=7.5, ha='right', va='bottom')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, color='#F1F5F9', fontsize=9)
        ax1.set_ylabel('Economy Rate (Lower = Better)', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax1.set_title(f"Phase Economy Rate ({scope_str})", fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
        ax1.set_ylim(0, max(10, max(p_econ, default=9) * 1.25))
        for b in bars1:
            h = b.get_height()
            ax1.text(b.get_x() + b.get_width()/2, h + 0.15, f"{h:.2f}", ha='center', va='bottom', fontsize=8, color='#E2E8F0', fontweight='bold')

        # 2. Dot Ball %
        bars2 = ax2.bar(x, p_dots, width=w, color=colors, zorder=2)
        ax2.axhline(40.0, color='#64748B', linestyle='--', lw=1.0, zorder=1)
        ax2.text(len(labels) - 0.5, 40.8, 'Benchmark (40%)', color='#94A3B8', fontsize=7.5, ha='right', va='bottom')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, color='#F1F5F9', fontsize=9)
        ax2.set_ylabel('Dot Ball % (Higher = Better)', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax2.set_title(f"Phase Dot Ball % ({scope_str})", fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
        ax2.set_ylim(0, max(50, max(p_dots, default=45) * 1.2))
        for b in bars2:
            h = b.get_height()
            ax2.text(b.get_x() + b.get_width()/2, h + 0.8, f"{h:.1f}%", ha='center', va='bottom', fontsize=8, color='#E2E8F0', fontweight='bold')

        # 3. Strike Rate (Balls / Wkt) & Wickets
        bars3 = ax3.bar(x, p_sr, width=w, color=colors, zorder=2)
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, color='#F1F5F9', fontsize=9)
        ax3.set_ylabel('Strike Rate (Balls/Wkt)', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax3.set_title(f"Phase Strike Rate & Wickets ({scope_str})", fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
        ax3.set_ylim(0, max(30, max(p_sr, default=24) * 1.25))
        for b, wkt in zip(bars3, p_wkts):
            h = b.get_height()
            ax3.text(b.get_x() + b.get_width()/2, h + 0.8, f"{h:.1f}\n({wkt}w)", ha='center', va='bottom', fontsize=7.5, color='#E2E8F0', fontweight='medium')

        fig.suptitle(f"{full_name} ({scope_str}) Across Phases",
                     fontsize=12, fontweight='bold', color='#F8FAFC', y=1.02)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', facecolor='#0B0F19')
    elif show_plot:
        plt.show()
    plt.close(fig)
    return True

splits = get_batter_matchup_splits('DP Conway', bowler_types=['SLA', 'OFF_SPIN'])
plot_matchup_phase_splits(splits, save_path='scratch/conway_phase_test.png')
print("Successfully generated scratch/conway_phase_test.png!")
