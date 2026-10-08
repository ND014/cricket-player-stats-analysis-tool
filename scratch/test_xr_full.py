import sqlite3
import pandas as pd

conn = sqlite3.connect('data/global_t20.db')

def compute_player_xr(cric_name, role='Batter', tournament='ALL'):
    conn = sqlite3.connect('data/global_t20.db')
    
    tourn_filter = ""
    params = [cric_name]
    if tournament and tournament != 'ALL':
        tourn_filter = " AND d.tournament = ? "
        params.append(tournament)
        
    is_bowler = (role == 'Bowler')
    
    if not is_bowler:
        q = f"""
            SELECT 
                d.match_id,
                d.start_date,
                d.venue,
                d.tournament,
                d.phase,
                d.runs_off_bat,
                mb.match_rpo,
                mb.par_score_20,
                mb.pitch_category,
                CASE 
                    WHEN d.phase = 'Powerplay' THEN mb.pp_rpb
                    WHEN d.phase = 'Middle' THEN mb.mid_rpb
                    WHEN d.phase = 'Death' THEN mb.dth_rpb
                    ELSE mb.match_rpb
                END as exp_rpb
            FROM deliveries d
            JOIN match_baselines mb ON d.match_id = mb.match_id
            WHERE d.striker = ? {tourn_filter}
        """
        df = pd.read_sql(q, conn, params=params)
        if len(df) == 0:
            return None
            
        total_balls = len(df)
        total_runs = int(df['runs_off_bat'].sum())
        total_xr = float(df['exp_rpb'].sum())
        run_value = total_runs - total_xr
        actual_sr = round(total_runs * 100.0 / total_balls, 1)
        expected_sr = round(total_xr * 100.0 / total_balls, 1)
        impact_ratio = round(total_runs / max(0.1, total_xr), 2)
        rv_per_100 = round(run_value * 100.0 / total_balls, 2)
        
        # Pitch category breakdown
        pitch_splits = []
        for pcat, label, desc, par_range in [
            ('HARD', 'Tough / Bowling Minefields', 'Sticky & turning pitches with Par < 155 (e.g. Mirpur, Chepauk turners, Lucknow)', '< 155'),
            ('BALANCED', 'Sporting / Balanced Decks', 'Standard competitive T20 surfaces with Par 155 – 184', '155 – 184'),
            ('EASY', 'Flat Highways / Batting Heavens', 'High-scoring roads with Par 185+ (e.g. Chinnaswamy, Wankhede, Hyderabad)', '185+')
        ]:
            sub = df[df['pitch_category'] == pcat]
            if len(sub) > 0:
                s_balls = len(sub)
                s_runs = int(sub['runs_off_bat'].sum())
                s_xr = float(sub['exp_rpb'].sum())
                s_rv = s_runs - s_xr
                s_matches = sub['match_id'].nunique()
                pitch_splits.append({
                    'category': pcat,
                    'label': label,
                    'desc': desc,
                    'par_range': par_range,
                    'matches': s_matches,
                    'balls': s_balls,
                    'runs': s_runs,
                    'xr': round(s_xr, 1),
                    'run_value': round(s_rv, 1),
                    'actual_sr': round(s_runs * 100.0 / s_balls, 1),
                    'expected_sr': round(s_xr * 100.0 / s_balls, 1),
                    'impact_ratio': round(s_runs / max(0.1, s_xr), 2)
                })
                
        # Phase splits
        phase_splits = []
        for ph in ['Powerplay', 'Middle', 'Death']:
            sub = df[df['phase'] == ph]
            if len(sub) > 0:
                s_balls = len(sub)
                s_runs = int(sub['runs_off_bat'].sum())
                s_xr = float(sub['exp_rpb'].sum())
                s_rv = s_runs - s_xr
                phase_splits.append({
                    'phase': ph,
                    'balls': s_balls,
                    'runs': s_runs,
                    'xr': round(s_xr, 1),
                    'run_value': round(s_rv, 1),
                    'actual_sr': round(s_runs * 100.0 / s_balls, 1),
                    'expected_sr': round(s_xr * 100.0 / s_balls, 1)
                })
                
        # Top impact innings
        match_agg = df.groupby(['match_id', 'venue', 'start_date', 'par_score_20', 'pitch_category']).agg(
            balls=('runs_off_bat', 'count'),
            runs=('runs_off_bat', 'sum'),
            xr=('exp_rpb', 'sum')
        ).reset_index()
        match_agg['run_value'] = match_agg['runs'] - match_agg['xr']
        match_agg['actual_sr'] = (match_agg['runs'] * 100.0 / match_agg['balls']).round(1)
        match_agg['par_sr'] = (match_agg['xr'] * 100.0 / match_agg['balls']).round(1)
        top_matches = match_agg[match_agg['balls'] >= 10].sort_values('run_value', ascending=False).head(5)
        top_innings = []
        for _, r in top_matches.iterrows():
            top_innings.append({
                'match_id': int(r['match_id']),
                'venue': r['venue'],
                'date': str(r['start_date'])[:10],
                'balls': int(r['balls']),
                'runs': int(r['runs']),
                'xr': round(float(r['xr']), 1),
                'run_value': round(float(r['run_value']), 1),
                'actual_sr': float(r['actual_sr']),
                'par_sr': float(r['par_sr']),
                'pitch_par': round(float(r['par_score_20']), 0),
                'pitch_category': r['pitch_category']
            })
            
        return {
            'role': 'Batter',
            'total_balls': total_balls,
            'total_runs': total_runs,
            'expected_runs': round(total_xr, 1),
            'run_value': round(run_value, 1),
            'actual_sr': actual_sr,
            'expected_sr': expected_sr,
            'impact_ratio': impact_ratio,
            'rv_per_100': rv_per_100,
            'pitch_splits': pitch_splits,
            'phase_splits': phase_splits,
            'top_innings': top_innings
        }
    else:
        # Bowler
        q = f"""
            SELECT 
                d.match_id,
                d.start_date,
                d.venue,
                d.tournament,
                d.phase,
                d.total_runs_conceded,
                d.is_wicket,
                mb.match_rpo,
                mb.par_score_20,
                mb.pitch_category,
                CASE 
                    WHEN d.phase = 'Powerplay' THEN mb.pp_rpb
                    WHEN d.phase = 'Middle' THEN mb.mid_rpb
                    WHEN d.phase = 'Death' THEN mb.dth_rpb
                    ELSE mb.match_rpb
                END as exp_rpb
            FROM deliveries d
            JOIN match_baselines mb ON d.match_id = mb.match_id
            WHERE d.bowler = ? {tourn_filter}
        """
        df = pd.read_sql(q, conn, params=params)
        if len(df) == 0:
            return None
            
        total_balls = len(df)
        overs = round(total_balls / 6.0, 1)
        total_conceded = int(df['total_runs_conceded'].sum())
        total_xrc = float(df['exp_rpb'].sum())
        runs_saved = total_xrc - total_conceded
        actual_econ = round(total_conceded / (total_balls / 6.0), 2)
        expected_econ = round(total_xrc / (total_balls / 6.0), 2)
        impact_ratio = round(total_xrc / max(0.1, total_conceded), 2)
        saved_per_match = round(runs_saved / max(1, (total_balls / 24.0)), 2)
        
        # Pitch category breakdown
        pitch_splits = []
        for pcat, label, desc, par_range in [
            ('HARD', 'Tough / Bowling Minefields', 'Low-scoring decks where par is < 155', '< 155'),
            ('BALANCED', 'Sporting / Balanced Decks', 'Standard competitive surfaces with Par 155 – 184', '155 – 184'),
            ('EASY', 'Flat Highways / Batting Paradises', 'High-scoring roads with Par 185+ (Tests bowler damage control)', '185+')
        ]:
            sub = df[df['pitch_category'] == pcat]
            if len(sub) > 0:
                s_balls = len(sub)
                s_conceded = int(sub['total_runs_conceded'].sum())
                s_xrc = float(sub['exp_rpb'].sum())
                s_saved = s_xrc - s_conceded
                s_matches = sub['match_id'].nunique()
                pitch_splits.append({
                    'category': pcat,
                    'label': label,
                    'desc': desc,
                    'par_range': par_range,
                    'matches': s_matches,
                    'balls': s_balls,
                    'runs_conceded': s_conceded,
                    'xrc': round(s_xrc, 1),
                    'runs_saved': round(s_saved, 1),
                    'actual_econ': round(s_conceded / (s_balls / 6.0), 2),
                    'expected_econ': round(s_xrc / (s_balls / 6.0), 2),
                    'impact_ratio': round(s_xrc / max(0.1, s_conceded), 2)
                })
                
        # Phase splits
        phase_splits = []
        for ph in ['Powerplay', 'Middle', 'Death']:
            sub = df[df['phase'] == ph]
            if len(sub) > 0:
                s_balls = len(sub)
                s_conceded = int(sub['total_runs_conceded'].sum())
                s_xrc = float(sub['exp_rpb'].sum())
                s_saved = s_xrc - s_conceded
                phase_splits.append({
                    'phase': ph,
                    'balls': s_balls,
                    'runs_conceded': s_conceded,
                    'xrc': round(s_xrc, 1),
                    'runs_saved': round(s_saved, 1),
                    'actual_econ': round(s_conceded / (s_balls / 6.0), 2),
                    'expected_econ': round(s_xrc / (s_balls / 6.0), 2)
                })
                
        # Top defense innings
        match_agg = df.groupby(['match_id', 'venue', 'start_date', 'par_score_20', 'pitch_category']).agg(
            balls=('total_runs_conceded', 'count'),
            conceded=('total_runs_conceded', 'sum'),
            xrc=('exp_rpb', 'sum'),
            wkts=('is_wicket', 'sum')
        ).reset_index()
        match_agg['runs_saved'] = match_agg['xrc'] - match_agg['conceded']
        match_agg['econ'] = (match_agg['conceded'] / (match_agg['balls'] / 6.0)).round(2)
        match_agg['par_econ'] = (match_agg['xrc'] / (match_agg['balls'] / 6.0)).round(2)
        top_matches = match_agg[match_agg['balls'] >= 12].sort_values('runs_saved', ascending=False).head(5)
        top_innings = []
        for _, r in top_matches.iterrows():
            top_innings.append({
                'match_id': int(r['match_id']),
                'venue': r['venue'],
                'date': str(r['start_date'])[:10],
                'balls': int(r['balls']),
                'runs_conceded': int(r['conceded']),
                'wkts': int(r['wkts']),
                'xrc': round(float(r['xrc']), 1),
                'runs_saved': round(float(r['runs_saved']), 1),
                'actual_econ': float(r['econ']),
                'par_econ': float(r['par_econ']),
                'pitch_par': round(float(r['par_score_20']), 0),
                'pitch_category': r['pitch_category']
            })
            
        return {
            'role': 'Bowler',
            'total_balls': total_balls,
            'overs': overs,
            'total_runs_conceded': total_conceded,
            'expected_runs_conceded': round(total_xrc, 1),
            'runs_saved': round(runs_saved, 1),
            'actual_econ': actual_econ,
            'expected_econ': expected_econ,
            'impact_ratio': impact_ratio,
            'saved_per_match': saved_per_match,
            'pitch_splits': pitch_splits,
            'phase_splits': phase_splits,
            'top_innings': top_innings
        }

print("=== BATTER XR TEST: KL Rahul ===")
kl = compute_player_xr('KL Rahul', 'Batter')
print("KL Rahul:", kl['total_runs'], "runs,", kl['expected_runs'], "xR, Run Value:", kl['run_value'], "SR:", kl['actual_sr'], "vs xSR:", kl['expected_sr'])
for p in kl['pitch_splits']:
    print(f"  {p['category']}: Balls {p['balls']} | Runs {p['runs']} | xR {p['xr']} | RV {p['run_value']:+0.1f} | SR {p['actual_sr']} vs {p['expected_sr']}")

print("\n=== BOWLER XR TEST: JJ Bumrah ===")
bum = compute_player_xr('JJ Bumrah', 'Bowler')
print("Bumrah:", bum['total_runs_conceded'], "conceded,", bum['expected_runs_conceded'], "xRC, Runs Saved:", bum['runs_saved'], "Econ:", bum['actual_econ'], "vs xEcon:", bum['expected_econ'])
for p in bum['pitch_splits']:
    print(f"  {p['category']}: Balls {p['balls']} | Conceded {p['runs_conceded']} | xRC {p['xrc']} | Saved {p['runs_saved']:+0.1f} | Econ {p['actual_econ']} vs {p['expected_econ']}")
