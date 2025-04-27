import requests

API_KEY = "d21699bfa8f4c7c1a94bb001a84f7c03"


def get_odds(fighter1, fighter2):
    url = f"https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds/?regions=us&markets=h2h,spreads,totals&apiKey={API_KEY}"

    response = requests.get(url)
    odds_data = response.json()

    odds = [None, None]
    
    for game in odds_data:
        if len(game['bookmakers']) > 0 and game['home_team'] == fighter1 and game['away_team'] == fighter2:
            for result in game['bookmakers'][0]['markets'][0]['outcomes']:
                if result['name'] == fighter1:
                    odds[0] = result['price']
                elif result['name'] == fighter2:
                    odds[1] = result['price']

    return odds



