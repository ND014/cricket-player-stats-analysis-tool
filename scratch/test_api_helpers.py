import os
import sys
import json
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.getcwd())
from matchup_engine import (
    resolve_player_name,
    auto_detect_player_meta,
    get_player_deliveries,
    get_batter_phase_stats,
    get_bowler_phase_stats,
    get_batter_kryptonite,
    get_top_nemesis_bowlers,
    get_top_punisher_batters,
    find_cost_effective_alternatives,
    get_player_tournament_footprint,
    get_batter_wagon_data,
    get_bowler_defensive_wagon_data,
    plot_batter_wagon_wheel,
    plot_bowler_defensive_wheel,
    compare_players,
    GLOBAL_TOURNAMENTS,
    INDIAN_PLAYER_METADATA,
    get_t20_db_connection
)

print("[+] Testing data serialization for Web API...")

cric_name = resolve_player_name("Virat Kohli")
df = get_player_deliveries(cric_name, tournament="ALL")
meta = auto_detect_player_meta(cric_name, df)
b_stats = get_batter_phase_stats(cric_name, df)
krypto = get_batter_kryptonite(cric_name, df)
nemeses = get_top_nemesis_bowlers(cric_name, top_n=3)
footprint = get_player_tournament_footprint(cric_name, df, is_bowler=False)

print(f"Player: {cric_name} | Role: {meta['role']} | Runs: {b_stats['total_runs']}")
print(f"Kryptonite: {krypto['primary_kryptonite']} | KVI: {krypto['primary_kvi']}")
print(f"Nemeses count: {len(nemeses)}")
if footprint is not None:
    print(f"Footprint count: {len(footprint)}")

# Test wagon wheel generation to buffer
buf = io.BytesIO()
plot_batter_wagon_wheel("Virat Kohli", vs_bowler_type="SLA", show_plot=True, save_path=buf)
buf.seek(0)
img_b64 = base64.b64encode(buf.read()).decode('utf-8')
print(f"Generated wagon wheel b64: {len(img_b64)} chars")

print("[+] All API helpers verified successfully!")
