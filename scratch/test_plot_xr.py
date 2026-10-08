import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def plot_xr_pitch_splits(xr_data, player_name, show_plot=False, save_path=None):
    if not xr_data or 'pitch_splits' not in xr_data:
        return None

    role = xr_data.get('role', 'Batter')
    is_bowler = (role == 'Bowler')
    pitch_splits = xr_data['pitch_splits']
    phase_splits = xr_data.get('phase_splits', [])

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 4.8), facecolor='#0B0F19')

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

    categories = [p['category'] for p in pitch_splits]
    cat_labels = [
        'Hard Pitch\n(Par < 155)' if c == 'HARD' else
        ('Balanced\n(Par 155-184)' if c == 'BALANCED' else 'Easy Highway\n(Par 185+)')
        for c in categories
    ]
    x = np.arange(len(categories))
    w = 0.35

    if not is_bowler:
        # --- BATTER ---
        # 1. SR vs Expected SR
        actual_srs = [p['actual_sr'] for p in pitch_splits]
        exp_srs = [p['expected_sr'] for p in pitch_splits]

        b1 = ax1.bar(x - w/2, actual_srs, width=w, label='Actual SR', color='#38BDF8', zorder=2)
        b2 = ax1.bar(x + w/2, exp_srs, width=w, label='Expected Par SR', color='#475569', zorder=2)
        ax1.set_xticks(x)
        ax1.set_xticklabels(cat_labels, fontsize=8.5, color='#F1F5F9')
        ax1.set_ylabel('Strike Rate', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax1.set_title('Strike Rate vs Pitch Par', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
        ax1.legend(facecolor='#1F2937', edgecolor='#374151', labelcolor='#D1D5DB', fontsize=8)
        max_y = max(max(actual_srs, default=150), max(exp_srs, default=150)) * 1.18
        ax1.set_ylim(0, max(160, max_y))

        for b in b1:
            ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 1.5, f"{b.get_height():.1f}",
                     ha='center', va='bottom', fontsize=8, color='#38BDF8', fontweight='bold')
        for b in b2:
            ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 1.5, f"{b.get_height():.1f}",
                     ha='center', va='bottom', fontsize=7.8, color='#94A3B8')

        # 2. Run Value (RAE) by Pitch Type
        rvs = [p['run_value'] for p in pitch_splits]
        rv_colors = ['#10B981' if v >= 0 else '#F43F5E' for v in rvs]
        b_rv = ax2.bar(x, rvs, width=0.48, color=rv_colors, zorder=2)
        ax2.axhline(0, color='#64748B', linestyle='-', lw=0.8, zorder=1)
        ax2.set_xticks(x)
        ax2.set_xticklabels(cat_labels, fontsize=8.5, color='#F1F5F9')
        ax2.set_ylabel('Runs Above Expected (RAE)', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax2.set_title('Net Run Value by Pitch Condition', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')

        for b, v in zip(b_rv, rvs):
            va = 'bottom' if v >= 0 else 'top'
            offset = 3.0 if v >= 0 else -3.0
            col = '#10B981' if v >= 0 else '#F43F5E'
            ax2.text(b.get_x() + b.get_width()/2, v + offset, f"{v:+0.1f}",
                     ha='center', va=va, fontsize=8.5, color=col, fontweight='bold')
        lim = max(abs(min(rvs, default=-10)), abs(max(rvs, default=10))) * 1.25
        ax2.set_ylim(-max(30, lim), max(30, lim))

        # 3. Phase Breakdown
        if phase_splits:
            ph_labels = [p['phase'] for p in phase_splits]
            ph_rvs = [p['run_value'] for p in phase_splits]
            ph_x = np.arange(len(ph_labels))
            ph_colors = ['#10B981' if v >= 0 else '#F43F5E' for v in ph_rvs]
            b_ph = ax3.bar(ph_x, ph_rvs, width=0.45, color=ph_colors, zorder=2)
            ax3.axhline(0, color='#64748B', linestyle='-', lw=0.8, zorder=1)
            ax3.set_xticks(ph_x)
            ax3.set_xticklabels(ph_labels, fontsize=8.5, color='#F1F5F9')
            ax3.set_ylabel('Run Value (RAE)', fontsize=8.5, color='#94A3B8', labelpad=6)
            ax3.set_title('Phase Value Generation (PP / Mid / Death)', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')

            for b, v in zip(b_ph, ph_rvs):
                va = 'bottom' if v >= 0 else 'top'
                offset = 2.5 if v >= 0 else -2.5
                col = '#10B981' if v >= 0 else '#F43F5E'
                ax3.text(b.get_x() + b.get_width()/2, v + offset, f"{v:+0.1f}",
                         ha='center', va=va, fontsize=8.5, color=col, fontweight='bold')
            ph_lim = max(abs(min(ph_rvs, default=-10)), abs(max(ph_rvs, default=10))) * 1.25
            ax3.set_ylim(-max(25, ph_lim), max(25, ph_lim))

        tot_rv = xr_data.get('run_value', 0.0)
        tot_col = "+ " if tot_rv >= 0 else ""
        fig.suptitle(f"{player_name} — Expected Runs (xR) & Pitch Difficulty Value Audit | Career RAE: {tot_col}{tot_rv:.1f} Runs",
                     fontsize=12, fontweight='bold', color='#F8FAFC', y=1.02)

    else:
        # --- BOWLER ---
        # 1. Economy vs Expected Economy
        actual_econs = [p['actual_econ'] for p in pitch_splits]
        exp_econs = [p['expected_econ'] for p in pitch_splits]

        b1 = ax1.bar(x - w/2, actual_econs, width=w, label='Actual Economy', color='#10B981', zorder=2)
        b2 = ax1.bar(x + w/2, exp_econs, width=w, label='Par Pitch Economy', color='#475569', zorder=2)
        ax1.set_xticks(x)
        ax1.set_xticklabels(cat_labels, fontsize=8.5, color='#F1F5F9')
        ax1.set_ylabel('Economy Rate (Lower = Better)', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax1.set_title('Economy Rate vs Pitch Par', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')
        ax1.legend(facecolor='#1F2937', edgecolor='#374151', labelcolor='#D1D5DB', fontsize=8)
        max_y = max(max(actual_econs, default=8), max(exp_econs, default=8)) * 1.25
        ax1.set_ylim(0, max(10, max_y))

        for b in b1:
            ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15, f"{b.get_height():.2f}",
                     ha='center', va='bottom', fontsize=8, color='#10B981', fontweight='bold')
        for b in b2:
            ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15, f"{b.get_height():.2f}",
                     ha='center', va='bottom', fontsize=7.8, color='#94A3B8')

        # 2. Runs Saved by Pitch Type
        saved = [p['runs_saved'] for p in pitch_splits]
        saved_colors = ['#10B981' if v >= 0 else '#F43F5E' for v in saved]
        b_s = ax2.bar(x, saved, width=0.48, color=saved_colors, zorder=2)
        ax2.axhline(0, color='#64748B', linestyle='-', lw=0.8, zorder=1)
        ax2.set_xticks(x)
        ax2.set_xticklabels(cat_labels, fontsize=8.5, color='#F1F5F9')
        ax2.set_ylabel('Runs Saved (Containment Surplus)', fontsize=8.5, color='#94A3B8', labelpad=6)
        ax2.set_title('Runs Saved by Pitch Condition', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')

        for b, v in zip(b_s, saved):
            va = 'bottom' if v >= 0 else 'top'
            offset = 4.0 if v >= 0 else -4.0
            col = '#10B981' if v >= 0 else '#F43F5E'
            ax2.text(b.get_x() + b.get_width()/2, v + offset, f"{v:+0.1f}",
                     ha='center', va=va, fontsize=8.5, color=col, fontweight='bold')
        lim = max(abs(min(saved, default=-10)), abs(max(saved, default=10))) * 1.25
        ax2.set_ylim(-max(30, lim), max(30, lim))

        # 3. Phase Breakdown
        if phase_splits:
            ph_labels = [p['phase'] for p in phase_splits]
            ph_saved = [p['runs_saved'] for p in phase_splits]
            ph_x = np.arange(len(ph_labels))
            ph_colors = ['#10B981' if v >= 0 else '#F43F5E' for v in ph_saved]
            b_ph = ax3.bar(ph_x, ph_saved, width=0.45, color=ph_colors, zorder=2)
            ax3.axhline(0, color='#64748B', linestyle='-', lw=0.8, zorder=1)
            ax3.set_xticks(ph_x)
            ax3.set_xticklabels(ph_labels, fontsize=8.5, color='#F1F5F9')
            ax3.set_ylabel('Runs Saved', fontsize=8.5, color='#94A3B8', labelpad=6)
            ax3.set_title('Phase Containment Value', fontsize=10.5, fontweight='bold', color='#F8FAFC', pad=12, loc='left')

            for b, v in zip(b_ph, ph_saved):
                va = 'bottom' if v >= 0 else 'top'
                offset = 3.0 if v >= 0 else -3.0
                col = '#10B981' if v >= 0 else '#F43F5E'
                ax3.text(b.get_x() + b.get_width()/2, v + offset, f"{v:+0.1f}",
                         ha='center', va=va, fontsize=8.5, color=col, fontweight='bold')
            ph_lim = max(abs(min(ph_saved, default=-10)), abs(max(ph_saved, default=10))) * 1.25
            ax3.set_ylim(-max(25, ph_lim), max(25, ph_lim))

        tot_s = xr_data.get('runs_saved', 0.0)
        tot_col = "+ " if tot_s >= 0 else ""
        fig.suptitle(f"{player_name} — Expected Runs Conceded (xRC) & Containment Value | Total Saved: {tot_col}{tot_s:.1f} Runs",
                     fontsize=12, fontweight='bold', color='#F8FAFC', y=1.02)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches='tight', facecolor='#0B0F19')
    elif show_plot:
        plt.show()
    plt.close(fig)
    return True

if __name__ == '__main__':
    from test_xr_full import compute_player_xr
    kl = compute_player_xr('KL Rahul', 'Batter')
    plot_xr_pitch_splits(kl, 'KL Rahul', save_path='scratch/kl_xr.png')
    bum = compute_player_xr('JJ Bumrah', 'Bowler')
    plot_xr_pitch_splits(bum, 'Jasprit Bumrah', save_path='scratch/bumrah_xr.png')
    print("Generated visual plots in scratch/")
