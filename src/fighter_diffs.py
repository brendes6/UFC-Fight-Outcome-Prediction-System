import pandas as pd
from data_cleaning import calculate_metrics, get_data_points
import os

def extract_fighter_stats():
    data = pd.read_csv("../Data/Cleaned/ufc-clean.csv")

    # Data points to extract
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

    fighter_df = pd.DataFrame(columns = values)

    fighters = set()

    # Iterate through fights in REVERSE chronological order
    for index, row in data.iterrows():
        if row["RedFighter"] not in fighters:
            fighters.add(row["RedFighter"])
            new_data = {}

            # For data points we need, get the value from the red fighter
            for val in values:
                new_data[val] = row["Red" + val]
            
            # Finding weight class - sensitive to weight misses
            if 120 < new_data["WeightLbs"] <= 130:
                new_data["WeightClass"] = "Flyweight"
            elif 130 < new_data["WeightLbs"] <= 140:
                new_data["WeightClass"] = "Bantamweight"
            elif 140 < new_data["WeightLbs"] <= 150:
                new_data["WeightClass"] = "Featherweight"
            elif 150 < new_data["WeightLbs"] <= 163:
                new_data["WeightClass"] = "Lightweight"
            elif 163 < new_data["WeightLbs"] <= 175:
                new_data["WeightClass"] = "Welterweight"
            elif 175 < new_data["WeightLbs"] <= 195:
                new_data["WeightClass"] = "Middleweight"
            elif 195 < new_data["WeightLbs"] <= 205:
                new_data["WeightClass"] = "Light Heavyweight"
            elif new_data["WeightLbs"] > 205:
                new_data["WeightClass"] = "Heavyweight"
            else:
                new_data["WeightClass"] = "Unknown"
                
            new_data["Gender"] = row["Gender"]
                
            fighter_df = pd.concat([fighter_df, pd.DataFrame([new_data])], ignore_index=True)
        if row["BlueFighter"] not in fighters:
            fighters.add(row["BlueFighter"])
            new_data = {}

            # For data points we need, get the value from the blue fighter
            for val in values:
                new_data[val] = row["Blue" + val]
            
            # Finding weight class - sensitive to weight misses
            if 120 < new_data["WeightLbs"] <= 130:
                new_data["WeightClass"] = "Flyweight"
            elif 130 < new_data["WeightLbs"] <= 140:
                new_data["WeightClass"] = "Bantamweight"
            elif 140 < new_data["WeightLbs"] <= 150:
                new_data["WeightClass"] = "Featherweight"
            elif 150 < new_data["WeightLbs"] <= 163:
                new_data["WeightClass"] = "Lightweight"
            elif 163 < new_data["WeightLbs"] <= 175:
                new_data["WeightClass"] = "Welterweight"
            elif 175 < new_data["WeightLbs"] <= 195:
                new_data["WeightClass"] = "Middleweight"
            elif 195 < new_data["WeightLbs"] <= 205:
                new_data["WeightClass"] = "Light Heavyweight"
            elif new_data["WeightLbs"] > 205:
                new_data["WeightClass"] = "Heavyweight"
            else:
                new_data["WeightClass"] = "Unknown"
            
            new_data["Gender"] = row["Gender"]
                
            fighter_df = pd.concat([fighter_df, pd.DataFrame([new_data])], ignore_index=True)
    
    fighter_df.to_csv("../Data/Cleaned/fighter-stats.csv", index=False)

    return fighter_df

def check_valid_fighter(fighter):
    current_script_dir = os.path.dirname(__file__)
    data_relative_path = os.path.join(current_script_dir, "..", "Data", "Cleaned", "fighter-stats.csv")

    data = pd.read_csv(data_relative_path)
    return fighter in data["Fighter"].values

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



    


if __name__ == "__main__":
    print(extract_fighter_stats())
    df = two_fighter_stats("Conor McGregor", "Dustin Poirier")
    
    
        

