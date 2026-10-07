import sys
sys.path.insert(0, '.')
from matchup_engine import get_bowler_defensive_wagon_data
data = get_bowler_defensive_wagon_data('DJ Bravo', phase='Death')
print('total_wkts reported in header:', data['total_wkts'])
print('len(data["wickets"]) markers array:', len(data['wickets']))
print('sum(summary["Wickets"]) across 8 sectors:', data['summary']['Wickets'].sum())
print('\nSector summary table:')
print(data['summary'][['Sector', 'FullName', 'RunsConceded', 'Wickets']])
