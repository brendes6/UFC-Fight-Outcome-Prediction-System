from data_cleaning import calculate_metrics
import os
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

# Get weight classes for the selected gender
def get_weight_classes(gender):
    if gender == "Female":
        return ["All", "Strawweight", "Flyweight", "Bantamweight"]
    else:
        return ["All", "Flyweight", "Bantamweight", "Featherweight", "Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"]
    

def get_all_fighters(weight_class, gender):
    current_script_dir = os.path.dirname(__file__)
    data_relative_path = os.path.join(current_script_dir, "..", "Data", "Cleaned", "fighter-stats.csv")

    data = pd.read_csv(data_relative_path)
    if not weight_class:
        weight_class = "All"
    if not gender:
        gender = "Male"
    if weight_class == "All":
        return data[data["Gender"] == gender.upper()]["Fighter"].sort_values(ascending=True)
    return data[(data["WeightClass"] == weight_class) & (data["Gender"] == gender.upper())]["Fighter"].sort_values(ascending=True)


def two_fighter_stats(fighter1, fighter2):
    current_script_dir = os.path.dirname(__file__)
    data_relative_path = os.path.join(current_script_dir, "..", "Data", "Cleaned", "fighter-stats.csv")

    data = pd.read_csv(data_relative_path)

    fighter1_data = data[data["Fighter"] == fighter1]
    fighter2_data = data[data["Fighter"] == fighter2]

    values = [
        "Fighter", "Wins", "WinsByKO", "WinsBySubmission", 
        "WinsByDecision", "Losses", "HeightCms", 
        "ReachCms", "AvgSigStrLanded", 
        "AvgTDLanded", "AvgSigStrPct", "AvgSubAtt", "Stance", 
        "WeightLbs", "Age", "KoPct", "SubPct",
        "DecPct", "AvgRounds", 
        "Elo", "OpponentElo", 
        "SigStrAbsorbed",
        "CurrentWinStreak",
        "FinishL5", "LossesByKO",
        "LossesBySub", "LossesByDec", "WinPct", "TotalRoundsFought"
    ]

    red_values = ["Red" + val for val in values]
    blue_values = ["Blue" + val for val in values]

    combined_values = red_values + blue_values

    combined_data = pd.DataFrame(columns = combined_values)

    new_data = {}

    filled_values = 0

    # Fill in red fighter data: val[3:] is the value without "Red"
    for val in red_values:
        if val[3:] in fighter1_data.columns: 
            new_data[val] = fighter1_data[val[3:]].iloc[0]
        else:
            new_data[val] = None
            filled_values += 1

    # Fill in blue fighter data: val[4:] is the value without "Blue"
    for val in blue_values:
        if val[4:] in fighter2_data.columns:
            new_data[val] = fighter2_data[val[4:]].iloc[0]
        else:
            new_data[val] = None
            filled_values += 1

    
    if not pd.DataFrame([new_data]).isna().all(axis=1).any():
        combined_data = pd.concat([combined_data, pd.DataFrame([new_data])], ignore_index=True)


    combined_data = calculate_metrics(combined_data, fighter_specific=True)

    if filled_values > 4:
        print(f"Warning: {filled_values} values were not found for {fighter1} and {fighter2}")

    return combined_data

@st.cache_data
def get_odds_data(red_fighter, blue_fighter):
    current_script_dir = os.path.dirname(__file__)
    html_relative_path = os.path.join(current_script_dir, "..", "html_files", "odds_file.html")
    with open(html_relative_path, 'r', encoding='utf-8') as f:
        html = f.read()

    bs = BeautifulSoup(html, 'html.parser')

    rows = bs.find_all('tr')

    odds = {
        "RedOdds": None,
        "BlueOdds": None,
        "RedSubOdds": None,
        "BlueSubOdds": None,
        "RedKOOdds": None,
        "BlueKOOdds": None,
        "RedDecOdds": None,
        "BlueDecOdds": None,
    }

    # Fighters last names
    red_fighter_name = red_fighter.split(" ")[1]
    blue_fighter_name = blue_fighter.split(" ")[1]


    for row in rows:
        # If the row contains the red fighter's name
        if row.text.find(red_fighter_name) > -1:
            if row.text.find(f"{red_fighter_name} wins by TKO/KO+") > -1:
                odds["RedKOOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by TKO/KO-") > -1:
                odds["RedKOOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by submission+") > -1:
                odds["RedSubOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by submission-") > -1:
                odds["RedSubOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by decision+") > -1:
                odds["RedDecOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by decision-") > -1:
                odds["RedDecOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name}+") > -1:
                odds["RedOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name}-") > -1:
                odds["RedOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
        # If the row contains the blue fighter's name
        elif row.text.find(blue_fighter_name) > -1:
            if row.text.find(f"{blue_fighter_name} wins by TKO/KO+") > -1:
                odds["BlueKOOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by TKO/KO-") > -1:
                odds["BlueKOOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by submission+") > -1:
                odds["BlueSubOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by submission-") > -1:
                odds["BlueSubOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by decision+") > -1:
                odds["BlueDecOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by decision-") > -1:
                odds["BlueDecOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name}+") > -1:
                odds["BlueOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name}-") > -1:
                odds["BlueOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])

    # If we have odds, calculat the 'either ...' odds
    if all(value != None for value in odds.values()):
        odds["EitherSubOdds"] = odds_conversion([implied_prob(odds["RedSubOdds"]) + implied_prob(odds["BlueSubOdds"])])[0]
        odds["EitherKOOdds"] = odds_conversion([implied_prob(odds["RedKOOdds"]) + implied_prob(odds["BlueKOOdds"])])[0]
        odds["EitherDecOdds"] = odds_conversion([implied_prob(odds["RedDecOdds"]) + implied_prob(odds["BlueDecOdds"])])[0]
        odds["RedSubBlueKO"] = odds_conversion([implied_prob(odds["RedSubOdds"]) + implied_prob(odds["BlueKOOdds"])])[0]
        odds["RedSubBlueDec"] = odds_conversion([implied_prob(odds["RedSubOdds"]) + implied_prob(odds["BlueDecOdds"])])[0]
        odds["RedKOBlueSub"] = odds_conversion([implied_prob(odds["RedKOOdds"]) + implied_prob(odds["BlueSubOdds"])])[0]
        odds["RedKOBlueDec"] = odds_conversion([implied_prob(odds["RedKOOdds"]) + implied_prob(odds["BlueDecOdds"])])[0]
        odds["RedDecBlueSub"] = odds_conversion([implied_prob(odds["RedDecOdds"]) + implied_prob(odds["BlueSubOdds"])])[0]
        odds["RedDecBlueKO"] = odds_conversion([implied_prob(odds["RedDecOdds"]) + implied_prob(odds["BlueKOOdds"])])[0]


    return odds


# Convert American odds to implied probability
def implied_prob(american_odds):
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return -american_odds / (-american_odds + 100)


def odds_conversion(predictions):
    # Convert percentage predictions to odds

    odds = []

    for prediction in predictions:
        if prediction == 0.5:
            odds.append("+100")
        elif prediction < 0.5:
            odds.append(f"+{(int(((1 - prediction) / prediction) * 100) // 10) * 10:.0f}")
        else:
            odds.append(f"{(int((-prediction / (1 - prediction)) * 100) // 10) * 10:.0f}")

    return odds


def check_valid_fighter(fighter1, fighter2):
    current_script_dir = os.path.dirname(__file__)
    data_relative_path = os.path.join(current_script_dir, "..", "Data", "Cleaned", "fighter-stats.csv")

    data = pd.read_csv(data_relative_path)

    if fighter1 not in data["Fighter"].values:
        return fighter1
    if fighter2 not in data["Fighter"].values:
        return fighter2
    return ""

def get_value_picks(odds_data, mean_outcome_pred, mean_winner_pred):

    values = ["RedOdds", "BlueOdds", "RedKOOdds", "RedSubOdds", 
              "RedDecOdds", "BlueKOOdds", "BlueSubOdds", "BlueDecOdds", 
              "EitherKOOdds", "RedKOBlueSub", "RedKOBlueDec",
              "RedSubBlueKO", "EitherSubOdds", "RedSubBlueDec",
              "RedDecBlueSub", "RedDecBlueKO", "EitherDecOdds"
              ]
    
    labels = [
        "Red to win", "Blue to win", "Red to win by KO/TKO", "Red to win by submission",
        "Red to win by decision", "Blue to win by KO/TKO", "Blue to win by submission", "Blue to win by decision",
        "Either fighter to win by KO/TKO", "Red to win by KO/TKO OR Blue to win by submission", "Red to win by KO/TKO OR Blue to win by decision",
        "Red to win by submission OR Blue to win by KO", "Either fighter to win by submission", "Red to win by submission OR Blue to win by decision",
        "Red to win by decision OR Blue to win by submission", "Red to win by decision OR Blue to win by KO/TKO", "Either fighter to win by decision"
    ]


    all_outcomes = [
        mean_winner_pred[0],
        mean_winner_pred[1],
        mean_outcome_pred[0],
        mean_outcome_pred[1],
        mean_outcome_pred[2],
        mean_outcome_pred[3],
        mean_outcome_pred[4],
        mean_outcome_pred[5],
        mean_outcome_pred[0] + mean_outcome_pred[3],
        mean_outcome_pred[0] + mean_outcome_pred[4],
        mean_outcome_pred[0] + mean_outcome_pred[5],
        mean_outcome_pred[1] + mean_outcome_pred[3],
        mean_outcome_pred[1] + mean_outcome_pred[4],
        mean_outcome_pred[1] + mean_outcome_pred[5],
        mean_outcome_pred[2] + mean_outcome_pred[3],
        mean_outcome_pred[2] + mean_outcome_pred[4],
        mean_outcome_pred[2] + mean_outcome_pred[5]
    ]

    picks = []

    for i in range(len(all_outcomes)):
            vegas_implied = implied_prob(int(odds_data[values[i]]))
            if all_outcomes[i]  - vegas_implied > 0.02:
                picks.append((labels[i] + f": Vegas says {vegas_implied*100:.1f}%, we say {all_outcomes[i]*100:.1f}%" , all_outcomes[i]  - vegas_implied))

    picks = sorted(picks, key=lambda x: x[1])[::-1]

    picks = [x[0] for x in picks]

    return picks[:3]