from sklearn.preprocessing import StandardScaler
import joblib


def get_X_y(df, prediction=False, known_odds=False, predicting_winner = False):
    """Get the feature matrix X and target vector y from the DataFrame.

    Input:
        df: DataFrame containing fight data.
        prediction: Boolean indicating if the function is used for prediction.
        known_odds: Boolean indicating if the odds data is known.
        predicting_winner: Boolean indicating if the model is predicting the winner.
    Output:
        X: Feature matrix.
        y: Target vector (if not prediction).
    """

    # Final features to pass into model
    final_features = [
        "RedWinPct", "BlueWinPct", "WinPctDif","RedKoPct", "BlueKoPct", "KoPctDif",
        "RedSubPct", "BlueSubPct", "SubPctDif","RedDecPct", "BlueDecPct", "DecPctDif","RedLossesByKO", "BlueLossesByKO", "LossesByKODif",
        "RedLossesBySub", "BlueLossesBySub", "LossesBySubDif","RedLossesByDec", "BlueLossesByDec", "LossesByDecDif", "RedWeightLbs",
        "HeightDif", "ReachDif", "AgeDif","RedAge", "BlueAge","SigStrDif", "StrPctDif", "TDDif", "SubAttDif",
        "RedAvgSigStrLanded", "BlueAvgSigStrLanded","RedAvgTDLanded", "BlueAvgTDLanded","RedAvgSigStrPct", "BlueAvgSigStrPct",
        "RedAvgSubAtt", "BlueAvgSubAtt","SigStrAbsorbedDif","RedSigStrAbsorbed", "BlueSigStrAbsorbed","AvgRoundsDif",
        "RedAvgRounds", "BlueAvgRounds","EloDif", "OpponentEloDif","RedElo", "BlueElo", "WinStreakDif",
        "RedCurrentWinStreak", "BlueCurrentWinStreak", "RedFinishL5", "BlueFinishL5", "FinishL5Dif","FinishPctDif"
    ]

    # If known odds, add odds features
    if known_odds:
        final_features.extend(["RedOdds", "BlueOdds"])


        X = df[final_features].copy()

        # fit + save scaler for known odds
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        joblib.dump((scaler, final_features), "../Models/Known_Odds/scaler.pkl")
        if not prediction:
            if predicting_winner:
                y = df["winner_number"].values
            else:
                y = df["categorical_outcome"].values
            return X_scaled, y
        else:
            return X_scaled
    else:
        X = df[final_features].copy()

        # fit + save scaler for unknown odds
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        joblib.dump((scaler, final_features), "../Models/Unknown_Odds/scaler.pkl")
        if not prediction:
            if predicting_winner:
                y = df["winner_number"].values
            else:
                y = df["categorical_outcome"].values
            return X_scaled, y
        else:
            return X_scaled
        
        