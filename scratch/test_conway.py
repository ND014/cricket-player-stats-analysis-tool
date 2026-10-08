import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from matchup_engine import get_batter_matchup_splits, get_player_full_name

splits = get_batter_matchup_splits('DP Conway', bowler_types=['SLA', 'OFF_SPIN'])
print("Splits summary:", splits['summary'])
print("Phases in splits:", splits['phases'])
print("Archetypes in splits:", [a['archetype'] for a in splits['archetypes']])
