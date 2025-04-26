import pandas as pd
import numpy as np


def get_elos_and_streaks(df):
    fighter_elos = {}
    opponent_elos = {}
    fighter_finish_l5 = {}
    fighter_loss_types = {}
    
    # Process fights in chronological order
    for index, row in df.iloc[::-1].iterrows():

        # Initialize fighter elos and opponent elos
        if row["RedFighter"] not in fighter_elos:
            fighter_elos[row["RedFighter"]] = 1500
            opponent_elos[row["RedFighter"]] = []
        if row["BlueFighter"] not in fighter_elos:
            fighter_elos[row["BlueFighter"]] = 1500
            opponent_elos[row["BlueFighter"]] = []

        # Initialize fighter finish l5 and fighter loss types
        if row["RedFighter"] not in fighter_finish_l5:
            fighter_finish_l5[row["RedFighter"]] = []
        if row["BlueFighter"] not in fighter_finish_l5:
            fighter_finish_l5[row["BlueFighter"]] = []
        if row["RedFighter"] not in fighter_loss_types:
            fighter_loss_types[row["RedFighter"]] = [0, 0, 0]
        if row["BlueFighter"] not in fighter_loss_types:
            fighter_loss_types[row["BlueFighter"]] = [0, 0, 0]

        opponent_elos[row["RedFighter"]].append(fighter_elos[row["BlueFighter"]])
        opponent_elos[row["BlueFighter"]].append(fighter_elos[row["RedFighter"]])

        # Update elos and streaks based on before-fight data from dictionaries
        df.at[index, "RedElo"] = fighter_elos[row["RedFighter"]]
        df.at[index, "BlueElo"] = fighter_elos[row["BlueFighter"]]
        df.at[index, "RedOpponentElo"] = np.mean(opponent_elos[row["RedFighter"]])
        df.at[index, "BlueOpponentElo"] = np.mean(opponent_elos[row["BlueFighter"]])
        if len(fighter_finish_l5[row["RedFighter"]]) < 5 and len(fighter_finish_l5[row["RedFighter"]]) > 0:
            ratio = 5 / len(fighter_finish_l5[row["RedFighter"]])
            df.at[index, "RedFinishL5"] = sum([n for n in fighter_finish_l5[row["RedFighter"]][-5:]]) * ratio
        else:
            df.at[index, "RedFinishL5"] = sum([n for n in fighter_finish_l5[row["RedFighter"]][-5:]])
        if len(fighter_finish_l5[row["BlueFighter"]]) < 5 and len(fighter_finish_l5[row["BlueFighter"]]) > 0:
            ratio = 5 / len(fighter_finish_l5[row["BlueFighter"]])
            df.at[index, "BlueFinishL5"] = sum([n for n in fighter_finish_l5[row["BlueFighter"]][-5:]]) * ratio
        else:
            df.at[index, "BlueFinishL5"] = sum([n for n in fighter_finish_l5[row["BlueFighter"]][-5:]])
        df.at[index, "RedLossesByKO"] = fighter_loss_types[row["RedFighter"]][0]
        df.at[index, "RedLossesBySub"] = fighter_loss_types[row["RedFighter"]][1]
        df.at[index, "RedLossesByDec"] = fighter_loss_types[row["RedFighter"]][2]
        df.at[index, "BlueLossesByKO"] = fighter_loss_types[row["BlueFighter"]][0]
        df.at[index, "BlueLossesBySub"] = fighter_loss_types[row["BlueFighter"]][1]
        df.at[index, "BlueLossesByDec"] = fighter_loss_types[row["BlueFighter"]][2]
        

        # Get expected values
        E1 = 1 / (1 + 10**((fighter_elos[row["BlueFighter"]] - fighter_elos[row["RedFighter"]]) / 400))
        E2 = 1 / (1 + 10**((fighter_elos[row["RedFighter"]] - fighter_elos[row["BlueFighter"]]) / 400))

        # Higher k value for finishes
        if row["Finish"] in ["KO/TKO", "Submission"]:
            k_value = 40
        elif row["Finish"] == "U-DEC":
            k_value = 30
        elif row["Finish"] == "S-DEC":
            k_value = 20
        else:
            k_value = 25

        # Update elos and streaks in dictionaries
        if row["Winner"] == "Red":
            fighter_elos[row["RedFighter"]] = fighter_elos[row["RedFighter"]] + k_value*(1-E1)
            fighter_elos[row["BlueFighter"]] = fighter_elos[row["BlueFighter"]] + k_value*(0-E2)
            if row["Finish"] in ["U-DEC", "S-DEC"]:
                fighter_finish_l5[row["RedFighter"]].append(0)
                fighter_loss_types[row["BlueFighter"]][2] += 1
            else:
                if row["Finish"] == "KO/TKO":
                    fighter_loss_types[row["BlueFighter"]][0] += 1
                elif row["Finish"] == "SUB":
                    fighter_loss_types[row["BlueFighter"]][1] += 1
                fighter_finish_l5[row["RedFighter"]].append(1)
        elif row["Winner"] == "Blue":
            fighter_elos[row["BlueFighter"]] = fighter_elos[row["BlueFighter"]] + k_value*(1-E2) 
            fighter_elos[row["RedFighter"]] = fighter_elos[row["RedFighter"]] + k_value*(0-E1)
            if row["Finish"] in ["U-DEC", "S-DEC"]:
                fighter_finish_l5[row["BlueFighter"]].append(0)
                fighter_loss_types[row["RedFighter"]][2] += 1
            else:
                if row["Finish"] == "KO/TKO":
                    fighter_loss_types[row["RedFighter"]][0] += 1
                elif row["Finish"] == "SUB":
                    fighter_loss_types[row["RedFighter"]][1] += 1
                fighter_finish_l5[row["BlueFighter"]].append(1)
    
    return df


def get_defense_data(df):
    defense_df = pd.read_csv("../Data/Raw/defense_data.csv")
    
    # Merge for red fighter
    df = df.merge(
        defense_df[['name', 'significant_strikes_absorbed_per_minute']],
        left_on='RedFighter',
        right_on='name',
        how='left'
    )
    df.rename(columns={'significant_strikes_absorbed_per_minute': 'RedSigStrAbsorbed'}, inplace=True)
    df.drop(columns=['name'], inplace=True)
    
    # Merge for blue fighter
    df = df.merge(
        defense_df[['name', 'significant_strikes_absorbed_per_minute']],
        left_on='BlueFighter',
        right_on='name',
        how='left'
    )
    df.rename(columns={'significant_strikes_absorbed_per_minute': 'BlueSigStrAbsorbed'}, inplace=True)
    df.drop(columns=['name'], inplace=True)

    return df


def calculate_metrics(df, fighter_specific=False):


    # Striking metrics
    df["StrikeTotal"] = df["RedAvgSigStrLanded"] + df["BlueAvgSigStrLanded"]
    df["StrikeAccuracyAvg"] = (df["RedAvgSigStrPct"] + df["BlueAvgSigStrPct"]) / 2

    # Finish percentages
    df["RedKoPct"] = df["RedWinsByKO"] / df["RedWins"]
    df["BlueKoPct"] = df["BlueWinsByKO"] / df["BlueWins"]
    df["RedSubPct"] = df["RedWinsBySubmission"] / df["RedWins"]
    df["BlueSubPct"] = df["BlueWinsBySubmission"] / df["BlueWins"]
    df["RedDecPct"] = df["RedWinsByDecision"] / df["RedWins"]
    df["BlueDecPct"] = df["BlueWinsByDecision"] / df["BlueWins"]
    df["RedFinishPct"] = (df["RedWinsByKO"] + df["RedWinsBySubmission"]) / df["RedWins"]
    df["BlueFinishPct"] = (df["BlueWinsByKO"] + df["BlueWinsBySubmission"]) / df["BlueWins"]
    df["FinishPctDif"] = df["RedFinishPct"] - df["BlueFinishPct"]
    df["AvgKoPct"] = (df["RedKoPct"] + df["BlueKoPct"]) / 2
    df["AvgSubPct"] = (df["RedSubPct"] + df["BlueSubPct"]) / 2
    df["AvgDecPct"] = (df["RedDecPct"] + df["BlueDecPct"]) / 2
    df["AvgAge"] = (df["RedAge"] + df["BlueAge"]) / 2
    df["AvgWinStreak"] = (df["RedCurrentWinStreak"] + df["BlueCurrentWinStreak"]) / 2
    
    # Round metrics
    df["RedAvgRounds"] = df["RedTotalRoundsFought"] / (df["RedWins"] + df["RedLosses"])
    df["BlueAvgRounds"] = df["BlueTotalRoundsFought"] / (df["BlueWins"] + df["BlueLosses"])

    # Differences
    df["SigStrDif"] = df["RedAvgSigStrLanded"] - df["BlueAvgSigStrLanded"]
    df["TDDif"] = df["RedAvgTDLanded"] - df["BlueAvgTDLanded"]
    df["SubAttDif"] = df["RedAvgSubAtt"] - df["BlueAvgSubAtt"]
    df["StrPctDif"] = df["RedAvgSigStrPct"] - df["BlueAvgSigStrPct"]
    df["WinStreakDif"] = df["RedCurrentWinStreak"] - df["BlueCurrentWinStreak"]
    df["WinDif"] = df["RedWins"] - df["BlueWins"]
    df["LossDiff"] = df["RedLosses"] - df["BlueLosses"]
    df["KODif"] = df["RedWinsByKO"] - df["BlueWinsByKO"]
    df["DecDif"] = df["RedWinsByDecision"] - df["BlueWinsByDecision"]
    df["SubDif"] = df["RedWinsBySubmission"] - df["BlueWinsBySubmission"]
    df["HeightDif"] = df["RedHeightCms"] - df["BlueHeightCms"]
    df["ReachDif"] = df["RedReachCms"] - df["BlueReachCms"]
    df["AgeDif"] = df["RedAge"] - df["BlueAge"]
    df["KoPctDif"] = df["RedKoPct"] - df["BlueKoPct"]
    df["SubPctDif"] = df["RedSubPct"] - df["BlueSubPct"]
    df["DecPctDif"] = df["RedDecPct"] - df["BlueDecPct"]
    df["AvgRoundsDif"] = df["RedAvgRounds"] - df["BlueAvgRounds"]
    df["ExperienceDif"] = (df["RedWins"] + df["RedLosses"]) - (df["BlueWins"] + df["BlueLosses"])
    df["EloDif"] = df["RedElo"] - df["BlueElo"]
    df["OpponentEloDif"] = df["RedOpponentElo"] - df["BlueOpponentElo"]
    df["FinishL5Dif"] = df["RedFinishL5"] - df["BlueFinishL5"]
    df["RedWinPct"] = df["RedWins"] / (df["RedWins"] + df["RedLosses"])
    df["BlueWinPct"] = df["BlueWins"] / (df["BlueWins"] + df["BlueLosses"])
    df["WinPctDif"] = df["RedWinPct"] - df["BlueWinPct"]
    df["LossesByKODif"] = df["RedLossesByKO"] - df["BlueLossesByKO"]
    df["LossesBySubDif"] = df["RedLossesBySub"] - df["BlueLossesBySub"]
    df["LossesByDecDif"] = df["RedLossesByDec"] - df["BlueLossesByDec"]
    df["SigStrAbsorbedDif"] = df["RedSigStrAbsorbed"] - df["BlueSigStrAbsorbed"]
    df["TotalSigStrAbsorbed"] = df["RedSigStrAbsorbed"] + df["BlueSigStrAbsorbed"]

    # Add winner and categorical outcome if not fighter specific
    if not fighter_specific:
        df.loc[(df["Finish"]=="U-DEC") | (df["Finish"] == "S-DEC"), "Finish"] = "DEC"
    
        df["categorical_outcome"] = 0
        df.loc[(df["Winner"] == "Red") & (df["Finish"] == "SUB"), "categorical_outcome"] = 1
        df.loc[(df["Winner"] == "Red") & (df["Finish"] == "KO/TKO"), "categorical_outcome"] = 0
        df.loc[(df["Winner"] == "Red") & (df["Finish"] == "DEC"), "categorical_outcome"] = 2
        df.loc[(df["Winner"] == "Blue") & (df["Finish"] == "SUB"), "categorical_outcome"] = 4
        df.loc[(df["Winner"] == "Blue") & (df["Finish"] == "KO/TKO"), "categorical_outcome"] = 3
        df.loc[(df["Winner"] == "Blue") & (df["Finish"] == "DEC"), "categorical_outcome"] = 5
        
        df["winner_number"] = 0
        df.loc[(df["Winner"] == "Red"), "winner_number"] = 1
        df.loc[(df["Winner"] == "Blue"), "winner_number"] = 2

    return df

def get_data_points(df):
    # Columns to keep in cleaned data
    data_points = [
        "RedFighter", "BlueFighter", "Winner", "WinnerName", 
        "Finish", "FinishDetails", "RedWins", "RedWinsByKO", "RedWinsBySubmission", 
        "RedWinsByDecision", "RedLosses", "BlueWins", "BlueWinsByKO", 
        "BlueWinsBySubmission", "BlueWinsByDecision", "BlueLosses", "RedHeightCms", 
        "BlueHeightCms", "RedReachCms", "BlueReachCms", "RedAvgSigStrLanded", 
        "RedAvgTDLanded", "RedAvgSigStrPct", "RedAvgSubAtt", "BlueAvgSigStrLanded", 
        "BlueAvgTDLanded", "BlueAvgSigStrPct", "BlueAvgSubAtt", "RedStance", 
        "BlueStance", "RedWeightLbs", "RedAge", "WinStreakDif", "WinDif", "LossDiff", 
        "KODif", "SubDif", "DecDif", "HeightDif", "ReachDif", "AgeDif", "SigStrDif", 
        "StrPctDif", "TDDif", "SubAttDif", "categorical_outcome", "winner_number",
        "StrikeTotal", "StrikeAccuracyAvg", "RedKoPct", "BlueKoPct", "RedSubPct", 
        "BlueSubPct", "RedDecPct", "BlueDecPct", "RedAvgRounds", "BlueAvgRounds", 
        "KoPctDif", "SubPctDif", "DecPctDif", "AvgRoundsDif", "ExperienceDif", 
        "RedElo", "BlueElo", "EloDif", "RedOpponentElo", "BlueOpponentElo",
        "OpponentEloDif", "RedSigStrAbsorbed", "BlueSigStrAbsorbed", 
        "SigStrAbsorbedDif", "FinishPctDif", "TotalSigStrAbsorbed", "AvgKoPct", 
        "AvgSubPct", "AvgDecPct", "AvgAge", "AvgWinStreak", "RedCurrentWinStreak",
        "BlueCurrentWinStreak", "RedFinishL5", "BlueFinishL5", "RedLossesByKO",
        "RedLossesBySub", "RedLossesByDec", "BlueLossesByKO", "BlueLossesBySub",
        "BlueLossesByDec", "BlueAge", "FinishL5Dif", "WinPctDif",
        "BlueWinPct", "RedWinPct", "LossesByKODif", "LossesBySubDif", "LossesByDecDif", "BlueWeightLbs", "RedTotalRoundsFought", "BlueTotalRoundsFought",
        "RedOdds", "BlueOdds", "RedDecOdds", "BlueDecOdds", "RSubOdds", "BSubOdds", "RKOOdds", "BKOOdds"
    ]
    
    # Remove rows with null values
    for column in data_points:
        if df[column].isnull().sum() > 0:
            print(f"{column} has {df[column].isnull().sum()} null values")
            df = df.dropna(subset=[column])
    
    # Select final columns
    df = df[data_points]

    return df


def clean_up_data(df):
    # Standardize decision wins
    df["RedWinsByDecision"] = df["RedWinsByDecisionUnanimous"] + df["RedWinsByDecisionMajority"] + df["RedWinsByDecisionSplit"]
    df["BlueWinsByDecision"] = df["BlueWinsByDecisionUnanimous"] + df["BlueWinsByDecisionMajority"] + df["BlueWinsByDecisionSplit"]
    
    # Add winner name
    df["WinnerName"] = df.apply(lambda row: row["RedFighter"] if row["Winner"] == "Red" else row["BlueFighter"], axis=1)
    
    # Fill missing values
    df["FinishDetails"] = df["FinishDetails"].fillna("No Finish")
    df["BlueStance"] = df["BlueStance"].fillna("Unknown")
    df["Finish"] = df["Finish"].fillna("Unknown")
    
    # Sig Strike numbers contain some data based on total strikes
    # rather than per minute, so we'll cap them at 10
    df = df[df["RedAvgSigStrLanded"] < 10]
    df = df[df["BlueAvgSigStrLanded"] < 10]
    
    return df


def get_clean_data():

    # Essentially pass data through all functions to clean it
    df = pd.read_csv("../Data/Raw/ufc-master.csv")
    df = clean_up_data(df)
    df = get_elos_and_streaks(df)
    df = get_defense_data(df)
    df = calculate_metrics(df)
    df = get_data_points(df)
    df.to_csv("../Data/Cleaned/ufc-clean.csv", index=False)

    return df


if __name__ == "__main__":
    df = get_clean_data()
    print(df.head())