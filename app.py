import os
import sys
import io
import re
import json
import base64
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask.json.provider import DefaultJSONProvider

class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, (np.integer, np.int64, np.int32)):
            return int(o)
        if isinstance(o, (np.floating, np.float64, np.float32)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        return super().default(o)

def sanitize_json(obj):
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [sanitize_json(x) for x in obj.tolist()]
    elif isinstance(obj, pd.DataFrame):
        return sanitize_json(obj.to_dict(orient='records'))
    elif isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_json(x) for x in obj]
    return obj

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from matchup_engine import (
    resolve_player_name,
    get_player_full_name,
    get_player_display_name,
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
    get_batter_matchup_splits,
    get_bowler_matchup_splits,
    plot_matchup_splits_comparison,
    GLOBAL_TOURNAMENTS,
    INDIAN_PLAYER_METADATA,
    get_t20_db_connection
)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.json = NumpyJSONProvider(app)

def _norm_phonetic(s: str) -> str:
    """Normalizes transliteration variations (oo<->u, ee<->i, w<->v) and removes punctuation."""
    s = str(s).lower().replace('w', 'v').replace('oo', 'u').replace('ee', 'i')
    s = re.sub(r'[^a-z0-9\s]', '', s)
    return re.sub(r'([a-z])\1+', r'\1', s).strip()

# Preload player list in-memory on startup for sub-millisecond search
PLAYERS_CACHE = []
def init_players_cache():
    global PLAYERS_CACHE
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'player_registry.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            players = data.get('players', [])
            players.sort(key=lambda x: x.get('deliveries', 0), reverse=True)
            PLAYERS_CACHE = [
                {
                    'name': p['full_name'],
                    'display': p['display'],
                    'cric_name': p['cric_name'],
                    'deliveries': p.get('deliveries', 0),
                    'aliases': [a.lower() for a in p.get('aliases', [])],
                    'norm_full': _norm_phonetic(p['full_name']),
                    'norm_cric': _norm_phonetic(p['cric_name']),
                    'norm_aliases': [_norm_phonetic(a) for a in p.get('aliases', [])]
                }
                for p in players
            ]
            print(f"[+] Web Server initialized with {len(PLAYERS_CACHE)} indexed players with full expanded names and alias registers.")
            return
        except Exception as e:
            print(f"[!] Warning: error reading player_registry.json: {e}")

    try:
        conn = get_t20_db_connection()
        rows = conn.execute("SELECT cric_name, full_name, display_name, deliveries, aliases_json FROM player_registry ORDER BY deliveries DESC").fetchall()
        PLAYERS_CACHE = [
            {
                'name': r[1],
                'display': r[2],
                'cric_name': r[0],
                'deliveries': r[3],
                'aliases': [a.lower() for a in json.loads(r[4])],
                'norm_full': _norm_phonetic(r[1]),
                'norm_cric': _norm_phonetic(r[0]),
                'norm_aliases': [_norm_phonetic(a) for a in json.loads(r[4])]
            }
            for r in rows
        ]
        print(f"[+] Web Server initialized from SQLite with {len(PLAYERS_CACHE)} indexed players.")
    except Exception as e:
        print(f"[!] Error loading players cache: {e}")

init_players_cache()


@app.route('/')
def index():
    return render_template('index.html', tournaments=GLOBAL_TOURNAMENTS)


@app.route('/api/tournaments')
def get_tournaments():
    return jsonify({
        'tournaments': GLOBAL_TOURNAMENTS,
        'count': len(GLOBAL_TOURNAMENTS)
    })


@app.route('/api/search')
def search_players():
    query = request.args.get('q', '').strip().lower()
    limit = int(request.args.get('limit', 12))
    if not query or len(query) < 1:
        return jsonify([])

    q_norm = _norm_phonetic(query)
    q_words = query.split()
    q_norm_words = [_norm_phonetic(w) for w in q_words if len(w) > 0]

    exact = []
    prefix_full = []
    prefix_cric = []
    prefix_alias = []
    substr_full = []
    substr_alias = []
    multi_token = []
    phonetic_match = []
    seen = set()

    for p in PLAYERS_CACHE:
        cric = p['cric_name']
        full = p['name'].lower()
        cric_l = cric.lower()
        aliases = p.get('aliases', [])
        norm_full = p.get('norm_full', full)
        norm_cric = p.get('norm_cric', cric_l)
        norm_aliases = p.get('norm_aliases', [])

        if query == full or query == cric_l or query in aliases:
            if cric not in seen:
                exact.append(p)
                seen.add(cric)
        elif full.startswith(query):
            if cric not in seen:
                prefix_full.append(p)
                seen.add(cric)
        elif cric_l.startswith(query):
            if cric not in seen:
                prefix_cric.append(p)
                seen.add(cric)
        elif any(a.startswith(query) for a in aliases):
            if cric not in seen:
                prefix_alias.append(p)
                seen.add(cric)
        elif query in full or query in cric_l:
            if cric not in seen:
                substr_full.append(p)
                seen.add(cric)
        elif any(query in a for a in aliases):
            if cric not in seen:
                substr_alias.append(p)
                seen.add(cric)
        elif len(q_words) >= 2 and all(w in full or w in cric_l or any(w in a for a in aliases) for w in q_words):
            if cric not in seen:
                multi_token.append(p)
                seen.add(cric)
        elif (q_norm == norm_full or q_norm == norm_cric or q_norm in norm_aliases
              or norm_full.startswith(q_norm) or any(na.startswith(q_norm) for na in norm_aliases)
              or (len(q_norm_words) >= 2 and all(nw in norm_full or nw in norm_cric or any(nw in na for na in norm_aliases) for nw in q_norm_words))):
            if cric not in seen:
                phonetic_match.append(p)
                seen.add(cric)

    ordered = exact + prefix_full + prefix_cric + prefix_alias + substr_full + substr_alias + multi_token + phonetic_match

    clean_results = [
        {
            'name': p['name'],
            'display': p['display'],
            'cric_name': p['cric_name'],
            'deliveries': p.get('deliveries', 0)
        }
        for p in ordered[:limit]
    ]
    return jsonify(clean_results)


@app.route('/api/census')
def get_database_census():
    conn = get_t20_db_connection()
    q = """
        SELECT 
            tournament AS Tournament,
            COUNT(DISTINCT match_id) AS Matches,
            COUNT(*) AS Deliveries,
            COUNT(DISTINCT striker) AS Batters,
            COUNT(DISTINCT bowler) AS Bowlers,
            MIN(start_date) AS Earliest_Match,
            MAX(start_date) AS Latest_Match
        FROM deliveries
        GROUP BY tournament
        ORDER BY Deliveries DESC
    """
    df = pd.read_sql(q, conn)
    data = []
    for _, r in df.iterrows():
        t_code = r['Tournament']
        meta = GLOBAL_TOURNAMENTS.get(t_code, {'name': t_code, 'country': 'Global', 'tier': 'Franchise'})
        data.append({
            'code': t_code,
            'name': meta.get('name', t_code),
            'country': meta.get('country', 'Global'),
            'tier': meta.get('tier', 'Franchise'),
            'matches': int(r['Matches']),
            'deliveries': int(r['Deliveries']),
            'batters': int(r['Batters']),
            'bowlers': int(r['Bowlers']),
            'span': f"{str(r['Earliest_Match'])[:4]} – {str(r['Latest_Match'])[:4]}"
        })
    return jsonify({
        'census': data,
        'total_matches': int(df['Matches'].sum()),
        'total_deliveries': int(df['Deliveries'].sum())
    })


@app.route('/api/player/audit')
def player_audit():
    player_query = request.args.get('name', 'Virat Kohli').strip()
    tournament = request.args.get('tournament', 'ALL').strip()
    
    cric_name = resolve_player_name(player_query)
    df = get_player_deliveries(cric_name, tournament=tournament)
    
    if len(df) == 0:
        return jsonify({'error': f"No deliveries found for '{player_query}' ({cric_name}) in tournament '{tournament}'."}), 404
        
    meta = auto_detect_player_meta(cric_name, df)
    role = meta.get('role', 'Batter')
    
    full_name = get_player_full_name(cric_name)
    disp_name = get_player_display_name(cric_name)

    res = {
        'player_query': player_query,
        'cric_name': cric_name,
        'full_name': full_name,
        'display_name': disp_name,
        'tournament': tournament,
        'tournament_name': GLOBAL_TOURNAMENTS.get(tournament, {}).get('name', tournament),
        'meta': meta,
        'total_deliveries': len(df)
    }
    
    is_bowler = (role == 'Bowler')
    is_all_rounder = (role == 'All-Rounder')
    balls_bowled = int(len(df[df['bowler'] == cric_name]))
    balls_batted = int(len(df[df['striker'] == cric_name]))
    # Threshold: 30 deliveries bowled = eligible for bowling stats tab (part-time bowlers included)
    BOWL_THRESHOLD = 30
    has_batting = role in ['Batter', 'All-Rounder'] or balls_batted >= 15
    has_bowling = role in ['Bowler', 'All-Rounder'] or balls_bowled >= BOWL_THRESHOLD
    is_part_time_bowler = has_bowling and role not in ['Bowler', 'All-Rounder']
    res['has_batting'] = has_batting
    res['has_bowling'] = has_bowling
    res['balls_bowled'] = balls_bowled
    res['balls_batted'] = balls_batted
    
    # 1. Batting Phase Stats
    if has_batting:
        bat_stats = get_batter_phase_stats(cric_name, df)
        res['batting_stats'] = bat_stats
        
        # Nemesis Bowlers
        nemeses = get_top_nemesis_bowlers(cric_name, top_n=3)
        if nemeses is not None:
            nem_records = nemeses.to_dict(orient='records')
            for r in nem_records:
                r['bowler_full'] = get_player_full_name(r.get('bowler', ''))
                r['bowler_display'] = get_player_display_name(r.get('bowler', ''))
            res['nemeses'] = nem_records
        else:
            res['nemeses'] = []
        
        # Kryptonite
        krypto = get_batter_kryptonite(cric_name, df)
        res['kryptonite'] = krypto
        
        # Batting Footprint
        bat_footprint = get_player_tournament_footprint(cric_name, df, is_bowler=False)
        res['batting_footprint'] = bat_footprint.to_dict(orient='records') if bat_footprint is not None else []
        
        # Batting Domestic Alternatives
        bat_alts = find_cost_effective_alternatives(cric_name, role='Batter')
        if bat_alts and isinstance(bat_alts, dict) and 'alts' in bat_alts:
            for a in bat_alts['alts']:
                if isinstance(a, dict):
                    a['full_name'] = get_player_full_name(a.get('player', ''))
                    a['display_name'] = get_player_display_name(a.get('player', ''))
        res['batting_alternatives'] = bat_alts
        
    # 2. Bowling Phase Stats
    if has_bowling:
        bowl_stats = get_bowler_phase_stats(cric_name, df)
        res['bowling_stats'] = bowl_stats
        
        # Punisher Batters
        punishers = get_top_punisher_batters(cric_name, top_n=3)
        if punishers is not None:
            pun_records = punishers.to_dict(orient='records')
            for r in pun_records:
                b_name = r.get('striker') or r.get('batter', '')
                r['batter'] = b_name
                r['batter_full'] = get_player_full_name(b_name)
                r['batter_display'] = get_player_display_name(b_name)
            res['punishers'] = pun_records
        else:
            res['punishers'] = []
        
        # Bowling Footprint
        bowl_footprint = get_player_tournament_footprint(cric_name, df, is_bowler=True)
        res['bowling_footprint'] = bowl_footprint.to_dict(orient='records') if bowl_footprint is not None else []
            
        # Bowling Domestic Alternatives
        bowl_alts = find_cost_effective_alternatives(cric_name, role='Bowler')
        if bowl_alts and isinstance(bowl_alts, dict) and 'alts' in bowl_alts:
            for a in bowl_alts['alts']:
                if isinstance(a, dict):
                    a['full_name'] = get_player_full_name(a.get('player', ''))
                    a['display_name'] = get_player_display_name(a.get('player', ''))
        res['bowling_alternatives'] = bowl_alts

    # Default fallback / legacy fields for footprint and alternatives
    if is_bowler:
        res['footprint'] = res.get('bowling_footprint', [])
        res['alternatives'] = res.get('bowling_alternatives')
    else:
        res['footprint'] = res.get('batting_footprint', [])
        res['alternatives'] = res.get('batting_alternatives')

    # 3. Initial Tactical Matchup Splits
    try:
        init_role = 'bowl' if role == 'Bowler' else 'bat'
        if init_role == 'bat':
            init_sp = get_batter_matchup_splits(cric_name, tournament=tournament)
        else:
            init_sp = get_bowler_matchup_splits(cric_name, tournament=tournament)
            
        if init_sp:
            buf = io.BytesIO()
            plt.close('all')
            plot_matchup_splits_comparison(init_sp, show_plot=True, save_path=buf)
            buf.seek(0)
            init_sp['image_b64'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close('all')
            init_sp['role'] = 'Batter' if init_role == 'bat' else 'Bowler'
            init_sp['active_role'] = init_role
            
        res['initial_splits'] = init_sp
    except Exception as e:
        print(f"[!] Error generating initial splits for {cric_name}: {e}")
        res['initial_splits'] = None

    return jsonify(sanitize_json(res))


@app.route('/api/player/splits')
def player_splits():
    name = request.args.get('name', 'Virat Kohli').strip()
    role = request.args.get('role', 'auto').strip().lower()
    types_raw = request.args.get('types', 'ALL').strip()
    hands_raw = request.args.get('hands', 'ALL').strip()
    phases_raw = request.args.get('phases', 'ALL').strip()
    tournament = request.args.get('tournament', 'ALL').strip()

    cric_name = resolve_player_name(name)
    df = get_player_deliveries(cric_name, tournament=tournament)
    if len(df) == 0:
        return jsonify({'error': f"No deliveries found for '{name}' ({cric_name}) in tournament '{tournament}'."}), 404

    meta = auto_detect_player_meta(cric_name, df)
    detected_role = meta.get('role', 'Batter')

    if role == 'auto':
        eff_role = 'bowl' if detected_role == 'Bowler' else 'bat'
    else:
        eff_role = 'bowl' if 'bowl' in role else 'bat'

    if eff_role == 'bat':
        types_list = [t.strip().upper() for t in types_raw.split(',') if t.strip()] if types_raw and types_raw != 'ALL' else None
        splits = get_batter_matchup_splits(cric_name, bowler_types=types_list, tournament=tournament)
    else:
        hands_list = [h.strip().upper() for h in hands_raw.split(',') if h.strip()] if hands_raw and hands_raw != 'ALL' else None
        phases_list = [p.strip() for p in phases_raw.split(',') if p.strip()] if phases_raw and phases_raw != 'ALL' else None
        splits = get_bowler_matchup_splits(cric_name, batter_hands=hands_list, phases=phases_list, tournament=tournament)

    if splits is None:
        return jsonify({'error': f"Could not generate matchup splits for '{cric_name}'."}), 404

    # Generate high-impact 3-panel comparative visual scorecard
    buf = io.BytesIO()
    plt.close('all')
    plot_matchup_splits_comparison(splits, show_plot=True, save_path=buf)
    buf.seek(0)
    splits['image_b64'] = base64.b64encode(buf.read()).decode('utf-8')
    plt.close('all')

    splits['player_query'] = name
    splits['meta'] = meta
    splits['detected_role'] = detected_role
    splits['active_role'] = eff_role
    splits['tournament'] = tournament

    return jsonify(sanitize_json(splits))


@app.route('/api/player/wagon')
def batter_wagon():
    player_query = request.args.get('name', 'Virat Kohli').strip()
    vs_bowler_type = request.args.get('bowler_type', 'ALL').strip()
    phase = request.args.get('phase', 'ALL').strip()
    tournament = request.args.get('tournament', 'ALL').strip()
    
    cric_name = resolve_player_name(player_query)
    data = get_batter_wagon_data(cric_name, vs_bowler_type=vs_bowler_type, phase=phase, tournament=tournament)
    
    if data is None:
        phase_str = f" in {phase} phase" if phase != 'ALL' else ""
        return jsonify({'error': f"No batting data found for {player_query} vs {vs_bowler_type}{phase_str} in {tournament}."}), 404
        
    # Generate high-res image
    buf = io.BytesIO()
    plt.close('all')
    plot_batter_wagon_wheel(cric_name, vs_bowler_type=vs_bowler_type, phase=phase, tournament=tournament, show_plot=True, save_path=buf)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close('all')
    
    summary_list = data['summary'].to_dict(orient='records')
    
    res = {
        'cric_name': cric_name,
        'player_query': player_query,
        'vs_bowler_type': vs_bowler_type,
        'phase': phase,
        'tournament': tournament,
        'is_lhb': data['is_lhb'],
        'total_runs': data['total_runs'],
        'total_balls': data['total_balls'],
        'overall_sr': data['overall_sr'],
        'total_dots': data['total_dots'],
        'total_fours': data['total_fours'],
        'total_sixes': data['total_sixes'],
        'summary': summary_list,
        'dominant_sector': summary_list[0] if summary_list else None,
        'image_b64': img_b64
    }
    return jsonify(sanitize_json(res))


@app.route('/api/player/defensive_wheel')
def bowler_defensive_wheel():
    player_query = request.args.get('name', 'Jasprit Bumrah').strip()
    phase = request.args.get('phase', 'ALL').strip()
    hand = request.args.get('hand', 'ALL').strip()
    tournament = request.args.get('tournament', 'ALL').strip()
    
    cric_name = resolve_player_name(player_query)
    data = get_bowler_defensive_wagon_data(cric_name, vs_batter_hand=hand, phase=phase, tournament=tournament)
    
    if data is None:
        return jsonify({'error': f"No bowling data found for {player_query} in phase '{phase}' in {tournament}."}), 404
        
    buf = io.BytesIO()
    plt.close('all')
    plot_bowler_defensive_wheel(cric_name, vs_batter_hand=hand, phase=phase, tournament=tournament, show_plot=True, save_path=buf)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close('all')
    
    summary_list = data['summary'].to_dict(orient='records')
    
    res = {
        'cric_name': cric_name,
        'player_query': player_query,
        'phase': phase,
        'hand': hand,
        'tournament': tournament,
        'total_runs_conceded': data['total_runs_conceded'],
        'total_balls': data['total_balls'],
        'total_overs': data['total_overs'],
        'overall_econ': data['overall_econ'],
        'overall_sr': data['overall_sr'],
        'total_wkts': data['total_wkts'],
        'summary': summary_list,
        'fortress_sector': summary_list[-1] if summary_list else None,
        'leak_sector': summary_list[0] if summary_list else None,
        'image_b64': img_b64
    }
    return jsonify(sanitize_json(res))


@app.route('/api/compare')
def player_comparison():
    p1 = request.args.get('player1', 'Virat Kohli').strip()
    p2 = request.args.get('player2', 'Rohit Sharma').strip()
    tournament = request.args.get('tournament', 'ALL').strip()
    req_mode = request.args.get('mode', 'auto').strip().lower().replace('/', '_vs_').replace('-', '_')
    vs_bowler_type = request.args.get('vs_bowler_type', 'ALL').strip().upper()
    vs_batter_hand = request.args.get('vs_batter_hand', 'ALL').strip().upper()
    
    c1 = resolve_player_name(p1)
    c2 = resolve_player_name(p2)
    conn = get_t20_db_connection()
    
    df1 = get_player_deliveries(c1, tournament=tournament)
    df2 = get_player_deliveries(c2, tournament=tournament)
    
    if len(df1) == 0:
        return jsonify({'error': f"No data found for {p1} ({c1}) in {tournament}."}), 404
    if len(df2) == 0:
        return jsonify({'error': f"No data found for {p2} ({c2}) in {tournament}."}), 404
        
    m1 = auto_detect_player_meta(c1, df1)
    m2 = auto_detect_player_meta(c2, df2)
    role1 = m1.get('role', 'Batter')
    role2 = m2.get('role', 'Batter')

    if req_mode not in ['auto', 'bat_vs_bat', 'bowl_vs_bowl', 'bat_vs_bowl', 'bowl_vs_bat']:
        req_mode = 'auto'

    if req_mode == 'auto':
        if role1 == 'Bowler' and role2 == 'Bowler':
            eff_mode = 'bowl_vs_bowl'
        elif role1 == 'Batter' and role2 == 'Bowler':
            eff_mode = 'bat_vs_bowl'
        elif role1 == 'Bowler' and role2 == 'Batter':
            eff_mode = 'bowl_vs_bat'
        elif role1 == 'Bowler' and role2 == 'All-Rounder':
            eff_mode = 'bowl_vs_bowl'
        elif role1 == 'All-Rounder' and role2 == 'Bowler':
            eff_mode = 'bowl_vs_bowl'
        else:
            eff_mode = 'bat_vs_bat'
    else:
        eff_mode = req_mode

    is_bowler_comp = (eff_mode == 'bowl_vs_bowl')
    is_duel = (eff_mode in ['bat_vs_bowl', 'bowl_vs_bat'])
    
    # Check H2H
    h2h_data = None
    has_h2h = False
    bat_c = None
    bowl_c = None
    if is_duel:
        bat_c = c1 if eff_mode == 'bat_vs_bowl' else c2
        bowl_c = c2 if eff_mode == 'bat_vs_bowl' else c1
        q_h2h = """
            SELECT 
                COUNT(*) as balls,
                SUM(runs_off_bat) as runs,
                SUM(CASE WHEN runs_off_bat = 0 THEN 1 ELSE 0 END) as dots,
                SUM(CASE WHEN runs_off_bat = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN runs_off_bat = 6 THEN 1 ELSE 0 END) as sixes,
                SUM(is_wicket) as dismissals
            FROM deliveries 
            WHERE striker = ? AND bowler = ?
        """
        df_h2h = pd.read_sql(q_h2h, conn, params=(bat_c, bowl_c))
        has_h2h = len(df_h2h) > 0 and int(df_h2h['balls'].values[0]) > 0
        if has_h2h:
            h_row = df_h2h.iloc[0]
            h2h_data = {
                'balls': int(h_row['balls']),
                'runs': int(h_row['runs']),
                'dots': int(h_row['dots']),
                'fours': int(h_row['fours']),
                'sixes': int(h_row['sixes']),
                'boundaries': int(h_row['fours'] + h_row['sixes']),
                'dismissals': int(h_row['dismissals']),
                'sr': round(int(h_row['runs']) * 100.0 / max(1, int(h_row['balls'])), 1),
                'dot_pct': round(int(h_row['dots']) * 100.0 / max(1, int(h_row['balls'])), 1),
                'batter': bat_c,
                'striker': bat_c,
                'bowler': bowl_c
            }
        
    buf = io.BytesIO()
    plt.close('all')
    compare_players(c1, c2, mode=eff_mode, vs_bowler_type=vs_bowler_type, vs_batter_hand=vs_batter_hand, tournament=tournament, show_plot=True, save_path=buf)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close('all')
    
    comp_type = 'bowler_vs_bowler' if is_bowler_comp else ('batter_vs_bowler_duel' if is_duel else 'batter_vs_batter')

    res = {
        'player1': {
            'query': p1,
            'cric_name': c1,
            'full_name': get_player_full_name(c1),
            'display_name': get_player_display_name(c1),
            'meta': m1
        },
        'player2': {
            'query': p2,
            'cric_name': c2,
            'full_name': get_player_full_name(c2),
            'display_name': get_player_display_name(c2),
            'meta': m2
        },
        'comparison_type': comp_type,
        'mode': eff_mode,
        'requested_mode': req_mode,
        'vs_bowler_type': vs_bowler_type,
        'vs_batter_hand': vs_batter_hand,
        'has_h2h': has_h2h,
        'h2h_data': h2h_data,
        'tournament': tournament,
        'image_b64': img_b64
    }
    
    if is_bowler_comp:
        res['b1_stats'] = get_bowler_phase_stats(c1, df1, vs_batter_hand=vs_batter_hand)
        res['b2_stats'] = get_bowler_phase_stats(c2, df2, vs_batter_hand=vs_batter_hand)
    elif is_duel:
        df_bat = df1 if eff_mode == 'bat_vs_bowl' else df2
        df_bowl = df2 if eff_mode == 'bat_vs_bowl' else df1
        res['bat_stats'] = get_batter_phase_stats(bat_c, df_bat, vs_bowler_type=vs_bowler_type)
        res['bowl_stats'] = get_bowler_phase_stats(bowl_c, df_bowl, vs_batter_hand=vs_batter_hand)
    else:
        res['p1_stats'] = get_batter_phase_stats(c1, df1, vs_bowler_type=vs_bowler_type)
        res['p2_stats'] = get_batter_phase_stats(c2, df2, vs_bowler_type=vs_bowler_type)
        
    return jsonify(sanitize_json(res))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n========================================================")
    print(f"[*] Starting Global T20 Analytics Web Application on port {port}")
    print(f"[*] Open http://localhost:{port} in your browser!")
    print(f"========================================================\n")
    app.run(host='0.0.0.0', port=port, debug=False)
