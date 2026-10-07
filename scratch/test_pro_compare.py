import os
import sys
sys.path.insert(0, os.getcwd())

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from matchup_engine import (
    resolve_player_name,
    auto_detect_player_meta,
    get_player_deliveries,
    get_batter_phase_stats,
    get_bowler_phase_stats,
    get_batter_kryptonite,
    get_t20_db_connection,
    GLOBAL_TOURNAMENTS
)

def test_pro_compare(player1="Virat Kohli", player2="Rohit Sharma", tournament="ALL"):
    c1 = resolve_player_name(player1)
    c2 = resolve_player_name(player2)
    conn = get_t20_db_connection()

    df1 = get_player_deliveries(c1, tournament=tournament)
    df2 = get_player_deliveries(c2, tournament=tournament)
    m1 = auto_detect_player_meta(c1, df1)
    m2 = auto_detect_player_meta(c2, df2)
    
    role1 = m1.get('role', 'Batter')
    role2 = m2.get('role', 'Batter')
    is_bowler_comp = (role1 == 'Bowler' and role2 == 'Bowler')
    
    q_h2h = """
        SELECT 
            COUNT(*) as balls,
            SUM(runs_off_bat) as runs,
            SUM(CASE WHEN runs_off_bat = 0 THEN 1 ELSE 0 END) as dots,
            SUM(CASE WHEN runs_off_bat = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN runs_off_bat = 6 THEN 1 ELSE 0 END) as sixes,
            SUM(is_wicket) as dismissals
        FROM deliveries 
        WHERE (striker = ? AND bowler = ?) OR (striker = ? AND bowler = ?)
    """
    df_h2h = pd.read_sql(q_h2h, conn, params=(c1, c2, c2, c1))
    has_h2h = len(df_h2h) > 0 and df_h2h['balls'].values[0] > 0
    h2h_data = df_h2h.iloc[0].to_dict() if has_h2h else None
    
    # 3-Panel Professional Card
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(17, 4.8), dpi=140)
    fig.patch.set_facecolor('#070B14')
    
    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor('#0F172A')
        for spine in ax.spines.values():
            spine.set_color('#1E293B')
            spine.set_linewidth(1.0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', color='#334155', linestyle=':', alpha=0.45, zorder=0)

    phases = ['Powerplay', 'Middle', 'Death']
    x = np.arange(len(phases))
    w = 0.35
    
    c1_color = '#38BDF8' # Sky Blue
    c2_color = '#F59E0B' # Amber Gold
    
    if is_bowler_comp:
        b1 = get_bowler_phase_stats(c1, df1)
        b2 = get_bowler_phase_stats(c2, df2)
        
        # Panel 1: Phase Economy
        e1 = [b1['phases'][p]['econ'] for p in phases]
        e2 = [b2['phases'][p]['econ'] for p in phases]
        b1_bars = ax1.bar(x - w/2, e1, w, label=c1, color=c1_color, edgecolor='white', linewidth=0.5, zorder=2)
        b2_bars = ax1.bar(x + w/2, e2, w, label=c2, color='#10B981', edgecolor='white', linewidth=0.5, zorder=2)
        ax1.axhline(8.2, color='#94A3B8', linestyle='--', lw=1.2, label='Par Econ (8.2)', zorder=1)
        ax1.set_xticks(x)
        ax1.set_xticklabels(phases, fontweight='bold', color='#F1F5F9', fontsize=9.5)
        ax1.set_ylabel('Economy Rate (Lower = Better)', fontsize=9, fontweight='bold', color='#94A3B8')
        ax1.set_title('PHASE ECONOMY SHOOTOUT', fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)
        ax1.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8.5)
        for b in b1_bars:
            ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15, f"{b.get_height():.2f}", ha='center', va='bottom', fontsize=8, color=c1_color, fontweight='bold')
        for b in b2_bars:
            ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15, f"{b.get_height():.2f}", ha='center', va='bottom', fontsize=8, color='#10B981', fontweight='bold')

        # Panel 2: Dot %
        d1 = [b1['phases'][p]['dot_pct'] for p in phases]
        d2 = [b2['phases'][p]['dot_pct'] for p in phases]
        ax2.bar(x - w/2, d1, w, label=c1, color=c1_color, edgecolor='white', linewidth=0.5, zorder=2)
        ax2.bar(x + w/2, d2, w, label=c2, color='#10B981', edgecolor='white', linewidth=0.5, zorder=2)
        ax2.set_xticks(x)
        ax2.set_xticklabels(phases, fontweight='bold', color='#F1F5F9', fontsize=9.5)
        ax2.set_ylabel('Dot Ball % (Higher = Better)', fontsize=9, fontweight='bold', color='#94A3B8')
        ax2.set_title('PHASE DOT BALL CHOKE %', fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)
        ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8.5)
        
        # Panel 3: Wickets
        w1 = [b1['phases'][p]['wickets'] for p in phases]
        w2 = [b2['phases'][p]['wickets'] for p in phases]
        ax3.bar(x - w/2, w1, w, label=c1, color=c1_color, edgecolor='white', linewidth=0.5, zorder=2)
        ax3.bar(x + w/2, w2, w, label=c2, color='#10B981', edgecolor='white', linewidth=0.5, zorder=2)
        ax3.set_xticks(x)
        ax3.set_xticklabels(phases, fontweight='bold', color='#F1F5F9', fontsize=9.5)
        ax3.set_ylabel('Total Wickets', fontsize=9, fontweight='bold', color='#94A3B8')
        ax3.set_title('PHASE WICKETS BREAKDOWN', fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)
        ax3.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8.5)

    else:
        p1_stats = get_batter_phase_stats(c1, df1)
        p2_stats = get_batter_phase_stats(c2, df2)
        
        # Panel 1: Phase Strike Rate
        s1 = [p1_stats['phases'][p]['sr'] for p in phases]
        s2 = [p2_stats['phases'][p]['sr'] for p in phases]
        b1_bars = ax1.bar(x - w/2, s1, w, label=c1, color=c1_color, edgecolor='white', linewidth=0.5, zorder=2)
        b2_bars = ax1.bar(x + w/2, s2, w, label=c2, color=c2_color, edgecolor='white', linewidth=0.5, zorder=2)
        ax1.axhline(135.0, color='#94A3B8', linestyle='--', lw=1.2, label='Par SR (135)', zorder=1)
        ax1.set_xticks(x)
        ax1.set_xticklabels(phases, fontweight='bold', color='#F1F5F9', fontsize=9.5)
        ax1.set_ylabel('Strike Rate', fontsize=9, fontweight='bold', color='#94A3B8')
        ax1.set_title('PHASE STRIKE RATE SHOOTOUT', fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)
        ax1.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8.5)
        for b in b1_bars:
            ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 2.5, f"{b.get_height():.1f}", ha='center', va='bottom', fontsize=8, color=c1_color, fontweight='bold')
        for b in b2_bars:
            ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 2.5, f"{b.get_height():.1f}", ha='center', va='bottom', fontsize=8, color=c2_color, fontweight='bold')

        # Panel 2: Dot Ball %
        dt1 = [p1_stats['phases'][p]['dot_pct'] for p in phases]
        dt2 = [p2_stats['phases'][p]['dot_pct'] for p in phases]
        ax2.bar(x - w/2, dt1, w, label=c1, color=c1_color, edgecolor='white', linewidth=0.5, zorder=2)
        ax2.bar(x + w/2, dt2, w, label=c2, color=c2_color, edgecolor='white', linewidth=0.5, zorder=2)
        ax2.set_xticks(x)
        ax2.set_xticklabels(phases, fontweight='bold', color='#F1F5F9', fontsize=9.5)
        ax2.set_ylabel('Dot Ball % (Lower = Better)', fontsize=9, fontweight='bold', color='#94A3B8')
        ax2.set_title('DOT BALL RESISTANCE %', fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)
        ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8.5)

        # Panel 3: Head-to-Head Duel or Boundary %
        if has_h2h:
            h_labels = ['Runs', 'Balls', 'Dots', '4s & 6s', 'Outs']
            h_vals = [h2h_data['runs'], h2h_data['balls'], h2h_data['dots'], h2h_data['fours'] + h2h_data['sixes'], h2h_data['dismissals']]
            h_cols = ['#38BDF8', '#818CF8', '#94A3B8', '#F59E0B', '#EF4444']
            h_bars = ax3.bar(h_labels, h_vals, color=h_cols, edgecolor='white', linewidth=0.5, width=0.52, zorder=2)
            ax3.set_title(f'HEAD-TO-HEAD DUEL: {c1} vs {c2}', fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)
            ax3.set_ylabel('Count', fontsize=9, fontweight='bold', color='#94A3B8')
            for b in h_bars:
                ax3.text(b.get_x() + b.get_width()/2, b.get_height() + 0.6, str(int(b.get_height())), ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#F8FAFC')
        else:
            b1_bnd = [p1_stats['phases'][p]['bnd_pct'] for p in phases]
            b2_bnd = [p2_stats['phases'][p]['bnd_pct'] for p in phases]
            ax3.bar(x - w/2, b1_bnd, w, label=c1, color=c1_color, edgecolor='white', linewidth=0.5, zorder=2)
            ax3.bar(x + w/2, b2_bnd, w, label=c2, color=c2_color, edgecolor='white', linewidth=0.5, zorder=2)
            ax3.set_xticks(x)
            ax3.set_xticklabels(phases, fontweight='bold', color='#F1F5F9', fontsize=9.5)
            ax3.set_ylabel('Boundary %', fontsize=9, fontweight='bold', color='#94A3B8')
            ax3.set_title('BOUNDARY CONVERSION %', fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)
            ax3.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8.5)

    plt.tight_layout()
    plt.savefig('scratch/test_pro_compare_rendered.png', bbox_inches='tight', facecolor='#070B14')
    print("Saved scratch/test_pro_compare_rendered.png successfully!")

test_pro_compare("Virat Kohli", "Rohit Sharma")
