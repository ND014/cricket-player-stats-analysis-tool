import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

conn = sqlite3.connect('data/global_t20.db')
c1, c2 = 'V Kohli', 'JJ Bumrah'

# 1. Fetch H2H deliveries
q = """
    SELECT 
        match_id, start_date, tournament, phase, over, ball,
        striker, bowler, runs_off_bat, total_runs_conceded,
        is_dot, is_boundary, is_wicket, wicket_type, player_dismissed
    FROM deliveries
    WHERE (striker = ? AND bowler = ?) OR (striker = ? AND bowler = ?)
    ORDER BY start_date, match_id, over, ball
"""
df_h2h = pd.read_sql(q, conn, params=(c1, c2, c2, c1))
balls_faced = len(df_h2h)
runs_scored = int(df_h2h['runs_off_bat'].sum())
dots = int((df_h2h['runs_off_bat'] == 0).sum())
fours = int((df_h2h['runs_off_bat'] == 4).sum())
sixes = int((df_h2h['runs_off_bat'] == 6).sum())
singles_doubles = int(((df_h2h['runs_off_bat'] > 0) & (df_h2h['runs_off_bat'] != 4) & (df_h2h['runs_off_bat'] != 6)).sum())
outs = int(df_h2h['is_wicket'].sum())
sr_h2h = round(runs_scored * 100.0 / max(1, balls_faced), 1)
dot_pct = round(dots * 100.0 / max(1, balls_faced), 1)

q_bat = "SELECT COUNT(*) as b, SUM(runs_off_bat) as r FROM deliveries WHERE striker = ?"
df_b = pd.read_sql(q_bat, conn, params=(c1,))
career_bat_sr = round(df_b['r'].values[0] * 100.0 / max(1, df_b['b'].values[0]), 1)

q_bowl = "SELECT COUNT(*) as b, SUM(total_runs_conceded) as r FROM deliveries WHERE bowler = ?"
df_bowl = pd.read_sql(q_bowl, conn, params=(c2,))
career_bowl_econ = round(df_bowl['r'].values[0] * 6.0 / max(1, df_bowl['b'].values[0]), 2)
duel_econ = round(df_h2h['total_runs_conceded'].sum() * 6.0 / max(1, balls_faced), 2)

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5.2), dpi=140)
fig.patch.set_facecolor('#070B14')

for ax in [ax1, ax2, ax3]:
    ax.set_facecolor('#0F172A')
    for s in ax.spines.values():
        s.set_color('#1E293B')
        s.set_linewidth(1.0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# PANEL 1: Donut
labels, values, colors = [], [], []
if dots > 0:
    labels.append(f'Dots ({dots})')
    values.append(dots)
    colors.append('#64748B')
if singles_doubles > 0:
    labels.append(f'1s/2s/3s ({singles_doubles})')
    values.append(singles_doubles)
    colors.append('#38BDF8')
if fours > 0:
    labels.append(f'4s ({fours})')
    values.append(fours)
    colors.append('#F59E0B')
if sixes > 0:
    labels.append(f'6s ({sixes})')
    values.append(sixes)
    colors.append('#A855F7')
if outs > 0:
    labels.append(f'Wickets ({outs})')
    values.append(outs)
    colors.append('#EF4444')

wedges, texts, autotexts = ax1.pie(
    values, labels=labels, colors=colors, autopct='%1.0f%%', pctdistance=0.75,
    startangle=140, wedgeprops=dict(width=0.42, edgecolor='#0F172A', linewidth=2.5),
    textprops=dict(color='#F1F5F9', fontsize=8.5, fontweight='bold')
)
for at in autotexts:
    at.set_color('#FFFFFF')
    at.set_fontsize(8)
    at.set_fontweight('bold')

ax1.text(0, 0.10, f"{sr_h2h}", ha='center', va='center', fontsize=18, fontweight='bold', color='#38BDF8')
ax1.text(0, -0.12, "MATCHUP SR", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#94A3B8')
ax1.text(0, -0.28, f"{runs_scored}r off {balls_faced}b • {outs} Out", ha='center', va='center', fontsize=8, fontweight='bold', color='#EF4444' if outs > 0 else '#10B981')
ax1.set_title(f"BALL ANATOMY ({c1} vs {c2})", fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)

# PANEL 2: Phase Breakdown
phase_stats = []
phases_list = ['Powerplay', 'Middle', 'Death']
for ph in phases_list:
    pdf = df_h2h[df_h2h['phase'] == ph]
    if len(pdf) > 0:
        p_runs = int(pdf['runs_off_bat'].sum())
        p_balls = len(pdf)
        p_outs = int(pdf['is_wicket'].sum())
        p_sr = round(p_runs * 100.0 / p_balls, 1)
        p_dots = int((pdf['runs_off_bat'] == 0).sum())
        phase_stats.append({
            'phase': ph, 'runs': p_runs, 'balls': p_balls, 'sr': p_sr, 'outs': p_outs, 'dots': p_dots
        })

if len(phase_stats) > 0:
    x_pos = np.arange(len(phase_stats))
    sr_vals = [p['sr'] for p in phase_stats]
    bars = ax2.bar(x_pos, sr_vals, color='#818CF8', width=0.42, edgecolor='white', linewidth=0.5, zorder=2)
    ax2.axhline(career_bat_sr, color='#38BDF8', linestyle='--', lw=1.2, label=f"Batter Career SR ({career_bat_sr})", zorder=1)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([f"{p['phase']}\n({p['runs']}r / {p['balls']}b, {p['outs']}w)" for p in phase_stats], fontweight='bold', color='#F1F5F9', fontsize=9)
    ax2.set_ylabel('Matchup Strike Rate', fontsize=9, fontweight='bold', color='#94A3B8')
    ax2.set_title("PHASE MATCHUP IMPACT", fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)
    ax2.grid(axis='y', color='#334155', linestyle=':', alpha=0.45, zorder=0)
    ax2.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8.5)
    for b in bars:
        ax2.text(b.get_x() + b.get_width()/2, b.get_height() + 2.5, f"{b.get_height():.1f} SR", ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#818CF8')

# PANEL 3: Benchmarks
bench_labels = ['Strike Rate', 'Economy Rate', 'Dot Ball %']
duel_metrics = [sr_h2h, duel_econ, dot_pct]
career_metrics = [career_bat_sr, career_bowl_econ, 35.0]

y_pos = np.arange(len(bench_labels))
bar_h = 0.32

ax3.barh(y_pos - bar_h/2, duel_metrics, bar_h, label='In Head-to-Head Duel', color=['#38BDF8', '#F59E0B', '#EF4444'], edgecolor='white', linewidth=0.5, zorder=2)
ax3.barh(y_pos + bar_h/2, career_metrics, bar_h, label='Career Benchmark', color='#475569', edgecolor='white', linewidth=0.5, zorder=2)

ax3.set_yticks(y_pos)
ax3.set_yticklabels(bench_labels, fontweight='bold', color='#F1F5F9', fontsize=9.5)
ax3.tick_params(axis='y', colors='#F1F5F9', labelsize=9.5)
ax3.tick_params(axis='x', colors='#94A3B8', labelsize=8.5)
ax3.grid(axis='x', color='#334155', linestyle=':', alpha=0.45, zorder=0)
ax3.set_title("MATCHUP vs CAREER BENCHMARKS", fontsize=11, fontweight='bold', color='#F8FAFC', pad=12)
ax3.legend(facecolor='#1E293B', edgecolor='#334155', labelcolor='#F8FAFC', fontsize=8.5)

for i in range(len(bench_labels)):
    d_val = duel_metrics[i]
    c_val = career_metrics[i]
    ax3.text(d_val + 2, i - bar_h/2, f"{d_val}", va='center', fontsize=8.5, fontweight='bold', color='#FFFFFF')
    ax3.text(c_val + 2, i + bar_h/2, f"{c_val}", va='center', fontsize=8.5, fontweight='bold', color='#94A3B8')

plt.tight_layout()
out_path = 'scratch/test_pro_duel_bumrah.png'
plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
plt.close('all')
print(f"Plot saved successfully to {out_path}")
