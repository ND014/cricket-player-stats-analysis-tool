import urllib.request
import json

def test():
    tests = [
        ("Bat vs Bat (RAF)", "http://127.0.0.1:5000/api/compare?player1=Virat%20Kohli&player2=Shubman%20Gill&mode=bat_vs_bat&vs_bowler_type=RAF"),
        ("Bowl vs Bowl (LHB)", "http://127.0.0.1:5000/api/compare?player1=Jasprit%20Bumrah&player2=Rashid%20Khan&mode=bowl_vs_bowl&vs_batter_hand=LHB"),
        ("Duel (Kohli vs Sandeep)", "http://127.0.0.1:5000/api/compare?player1=Virat%20Kohli&player2=Sandeep%20Sharma&mode=auto")
    ]
    for label, url in tests:
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode('utf-8'))
        print(f"[{label}]")
        print(f"  comparison_type: {data.get('comparison_type')}")
        print(f"  mode: {data.get('mode')}")
        print(f"  vs_bowler_type: {data.get('vs_bowler_type')}")
        print(f"  vs_batter_hand: {data.get('vs_batter_hand')}")
        print(f"  has_h2h: {data.get('has_h2h')}")
        if data.get('comparison_type') == 'bowler_vs_bowler':
            b1 = data.get('b1_stats')
            b2 = data.get('b2_stats')
            print(f"  Bumrah wkts vs LHB: {b1.get('total_wickets')}, econ: {b1.get('overall_econ')}")
            print(f"  Rashid wkts vs LHB: {b2.get('total_wickets')}, econ: {b2.get('overall_econ')}")
        elif data.get('comparison_type') == 'batter_vs_batter':
            p1 = data.get('p1_stats')
            p2 = data.get('p2_stats')
            print(f"  Kohli runs vs RAF: {p1.get('total_runs')}, sr: {p1.get('overall_sr')}")
            print(f"  Gill runs vs RAF: {p2.get('total_runs')}, sr: {p2.get('overall_sr')}")
        elif data.get('comparison_type') == 'batter_vs_bowler_duel':
            h2h = data.get('h2h_data')
            print(f"  H2H balls: {h2h.get('balls')}, runs: {h2h.get('runs')}, dismissals: {h2h.get('dismissals')}")
        print()

if __name__ == '__main__':
    test()
