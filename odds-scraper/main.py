import requests
from google.cloud import firestore
import os
from dotenv import load_dotenv
import json
load_dotenv()

API_URL = f"https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds?regions=us&apiKey={os.getenv('ODDS_API_KEY')}"


def price_to_pct_chance(price_val):
    # Convert price (e.g. Khamzat Chimaev 1.56) to percent change (Chimaev 78%)
    
    return round((1 / price_val), 3)

def update_odds():
    # Get upcoming odds from The Odds API

    # 1 - Load all MMA odds
    print("Starting to get odds...")

    try:
        response = requests.get(API_URL)
        odds = response.json()
        json_string = json.dumps(odds)
        with open("odds.json", "w") as f:
            f.write(json_string)
    except Exception as e:
        print(e)
        return

    print("Odds Loaded\n")

    # 2 - Create red/blue tags for each fighter

    print("Creating matchup odds...")

    matchup_odds = {}

    for fight in odds:

        if not fight["bookmakers"]:
            continue

        first_entry = fight["bookmakers"][0]

        if not first_entry["markets"]:
            continue
        
        market = first_entry["markets"][0]
    
        if market["key"] == "h2h" and market["outcomes"]:

            red_fighter = market["outcomes"][0]["name"]
            blue_fighter = market["outcomes"][1]["name"]

            red_tag = red_fighter.replace("-", " ").lower().split()
            if red_tag[-1] in ["jr", "sr", "jr.", "sr."]:
                red_tag = "_".join(red_tag[:-1])
            else:
                red_tag = "_".join(red_tag)

            blue_tag = blue_fighter.replace("-", " ").lower().split()
            if blue_tag[-1] in ["jr", "sr", "jr.", "sr."]:
                blue_tag = "_".join(blue_tag[:-1])
            else:
                blue_tag = "_".join(blue_tag)

            red_prob = price_to_pct_chance(market["outcomes"][0]["price"])
            blue_prob = price_to_pct_chance(market["outcomes"][1]["price"])

            adjustment_factor = 100 / ((red_prob + blue_prob) * 100)

            red_prob = red_prob * adjustment_factor
            blue_prob = blue_prob * adjustment_factor

            key1 = red_tag + "_" + blue_tag

            matchup_odds[key1] = (red_prob, blue_prob)

    print("Matchup odds: ", matchup_odds)
    print("Got matchup odds.\n")
    
    # 3 - Iterate table entries and add odds

    print("Adding odds to database...")

    db = firestore.Client(project="ufc-proj", database="ufcdb")
        
    upcoming_ref = db.collection("upcoming")
    docs = upcoming_ref.stream()

    for doc in docs:
        key1 = doc.get("red_tag") + "_" + doc.get("blue_tag")
        key2 = doc.get("blue_tag") + "_" + doc.get("red_tag")

        red_win = doc.get("red_win")
        blue_win = doc.get("blue_win")
        
        red_prob, blue_prob, red_ev, blue_ev, best_bet, best_bet_ev = None, None, None, None, None, None
        
        if key1 in matchup_odds:
            print("key: ", key1)
            red_prob = matchup_odds[key1][0]
            blue_prob = matchup_odds[key1][1]

            if red_win > (red_prob + 0.1):
                red_ev = round(red_win - red_prob, 3)
                best_bet = "Red"
                best_bet_ev = red_ev
            elif blue_win > (blue_prob + 0.1):
                blue_ev = round(blue_win - blue_prob, 3)
                best_bet = "Blue"
                best_bet_ev = blue_ev

        elif key2 in matchup_odds:  
            print("key: ", key2)
            red_prob = matchup_odds[key2][1]
            blue_prob = matchup_odds[key2][0]

            if red_win > (red_prob + 0.1):
                red_ev = round(red_win - red_prob, 3)
                best_bet = "Red"
                best_bet_ev = red_ev
            elif blue_win > (blue_prob + 0.1):
                blue_ev = round(blue_win - blue_prob, 3)
                best_bet = "Blue"
                best_bet_ev = blue_ev

        doc.reference.update({
            "red_prob": red_prob,
            "blue_prob": blue_prob,
            "red_ev": red_ev,
            "blue_ev": blue_ev,
            "best_bet": best_bet,
            "best_bet_ev": best_bet_ev,
        })

    print("Added odds to database.")



if __name__ == "__main__":
    update_odds()