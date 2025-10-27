import pandas as pd
from services.db import crud, database

def two_fighter_stats(fighter1, fighter2):
    """Get the stats for two fighters from the cleaned fighter stats CSV file.
    
    Input:
        fighter1: Name of the first fighter.
        fighter2: Name of the second fighter.   
    Output:
        A DataFrame containing the stats for both fighters.
    """
    # Get our database and both fighters data
    db = next(database.get_db())

    fighter1_data = crud.get_fighter_by_name(db, fighter1)
    fighter2_data = crud.get_fighter_by_name(db, fighter2)

    if fighter1_data is None:
        raise ValueError(f"Fighter {fighter1} not found in database.")
    if fighter2_data is None:
        raise ValueError(f"Fighter {fighter2} not found in database.")

    # Use 2 different lists for dataframe vs database values
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

    db_vals = [
        "name",
        "wins", 
        "wins_by_ko",
        "wins_by_submission",
        "wins_by_decision",
        "losses",
        "height_cms",
        "reach_cms",
        "avg_sig_str_landed",
        "avg_td_landed",
        "avg_sig_str_pct",
        "avg_sub_att",
        "stance",
        "weight_lbs",
        "age",
        "ko_pct",
        "sub_pct",
        "dec_pct",
        "avg_rounds",
        "elo",
        "opponent_elo",
        "sig_str_absorbed",
        "current_win_streak",
        "finish_l5",
        "losses_by_ko",
        "losses_by_sub",
        "losses_by_dec",
        "win_pct",
        "total_rounds_fought",
    ]

    # Map red and blue values
    mapping = dict(zip(values, db_vals))

    red_values = ["Red" + val for val in values]
    blue_values = ["Blue" + val for val in values]

    combined_values = red_values + blue_values

    combined_data = pd.DataFrame(columns = combined_values)

    new_data = {}

    # Red fighter
    for val in values:
        db_field = mapping[val]
        new_data["Red" + val] = getattr(fighter1_data, db_field)

    # Blue fighter
    for val in values:
        db_field = mapping[val]
        new_data["Blue" + val] = getattr(fighter2_data, db_field)


    
    # Combine dataframes, calculate metrics for fighters
    if not pd.DataFrame([new_data]).isna().all(axis=1).any():
        combined_data = pd.concat([combined_data, pd.DataFrame([new_data])], ignore_index=True)


    combined_data = calculate_metrics(combined_data, fighter_specific=True)


    return combined_data



def calculate_metrics(df, fighter_specific=False):
    """Calculate various metrics for fighters in the DataFrame.

    Input:
        df: DataFrame containing fight data
        fighter_specific: Boolean indicating if the metrics are for specific fighters
    Output:
        DataFrame with calculated metrics added.
    """


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
        df.loc[(df["Winner"] == "Red"), "winner_number"] = 0
        df.loc[(df["Winner"] == "Blue"), "winner_number"] = 1

    return df