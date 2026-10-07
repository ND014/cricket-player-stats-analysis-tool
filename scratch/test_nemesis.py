import sqlite3
import pandas as pd

conn = sqlite3.connect('data/global_t20.db')

def get_top_nemesis_bowlers(batter_name, top_n=3):
    q_tot = 'SELECT count(*) FROM deliveries WHERE striker = ?'
    tot = conn.execute(q_tot, (batter_name,)).fetchone()[0]
    min_b = max(12, int(tot * 0.005))
    q = '''
        SELECT 
            bowler,
            bowler_archetype,
            COUNT(is_legal_ball) as balls,
            SUM(runs_off_bat) as runs,
            SUM(is_dot) as dots,
            SUM(is_wicket) as dismissals,
            ROUND(SUM(runs_off_bat)*100.0/COUNT(is_legal_ball), 1) as sr,
            ROUND(SUM(is_dot)*100.0/COUNT(is_legal_ball), 1) as dot_pct
        FROM deliveries
        WHERE striker = ?
        GROUP BY bowler
        HAVING balls >= ?
    '''
    df = pd.read_sql(q, conn, params=(batter_name, min_b))
    if len(df) == 0: return df
    df['nemesis_score'] = (df['dismissals'] * 30.0) + (140.0 - df['sr']).clip(lower=0) + (df['dot_pct'] * 0.5)
    return df.sort_values(by=['dismissals', 'nemesis_score'], ascending=[False, False]).head(top_n)

def get_top_punisher_batters(bowler_name, top_n=3):
    q_tot = 'SELECT count(*) FROM deliveries WHERE bowler = ?'
    tot = conn.execute(q_tot, (bowler_name,)).fetchone()[0]
    min_b = max(12, int(tot * 0.005))
    q = '''
        SELECT 
            striker,
            COUNT(is_legal_ball) as balls,
            SUM(runs_off_bat) as runs,
            SUM(is_boundary) as boundaries,
            SUM(is_wicket) as dismissals,
            ROUND(SUM(runs_off_bat)*100.0/COUNT(is_legal_ball), 1) as sr,
            ROUND(SUM(is_boundary)*100.0/COUNT(is_legal_ball), 1) as bnd_pct
        FROM deliveries
        WHERE bowler = ?
        GROUP BY striker
        HAVING balls >= ?
    '''
    df = pd.read_sql(q, conn, params=(bowler_name, min_b))
    if len(df) == 0: return df
    df['punisher_score'] = df['sr'] + (df['bnd_pct'] * 1.5) - (df['dismissals'] * 15.0)
    return df.sort_values(by='punisher_score', ascending=False).head(top_n)

print('--- NEMESIS BOWLERS FOR ROHIT SHARMA ---')
for _, r in get_top_nemesis_bowlers('RG Sharma').iterrows():
    print(f"  {r['bowler']} ({r['bowler_archetype']}): {int(r['balls'])} balls | {int(r['runs'])} runs | {int(r['dismissals'])} OUTS | {r['sr']} SR | {r['dot_pct']}% dots")

print('\n--- PUNISHER BATTERS FOR JASPRIT BUMRAH ---')
for _, r in get_top_punisher_batters('JJ Bumrah').iterrows():
    print(f"  {r['striker']}: {int(r['balls'])} balls | {int(r['runs'])} runs | {int(r['boundaries'])} boundaries | {int(r['dismissals'])} OUTS | {r['sr']} SR")

print('\n--- ANDRE RUSSELL (ALL-ROUNDER DUAL AUDIT) ---')
print('When Batting (Nemesis Bowlers):')
for _, r in get_top_nemesis_bowlers('AD Russell').iterrows():
    print(f"  {r['bowler']} ({r['bowler_archetype']}): {int(r['balls'])} balls | {int(r['dismissals'])} OUTS | {r['sr']} SR | {r['dot_pct']}% dots")
print('When Bowling (Punisher Batters):')
for _, r in get_top_punisher_batters('AD Russell').iterrows():
    print(f"  {r['striker']}: {int(r['balls'])} balls | {int(r['runs'])} runs | {r['sr']} SR | {int(r['dismissals'])} OUTS")
