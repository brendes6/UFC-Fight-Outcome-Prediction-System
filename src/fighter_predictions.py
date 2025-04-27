import pandas as pd
import numpy as np
import torch
from fighter_diffs import two_fighter_stats
from feature_engineering import get_X_y
import joblib
from model import predict, build_model
from fighter_diffs import check_valid_fighter
from get_odds import get_odds
import os

def odds_conversion(predictions, from_type="decimal", for_prediction=False):
    # Convert percentage predictions to odds

    odds = []

    for prediction in predictions:
        if from_type == "decimal":
            if prediction >= 2.0:
                if for_prediction:
                    odds.append(int((prediction - 1) * 100))
                else:
                    odds.append(f"+{int((prediction - 1) * 100):.0f}")
            else:
                if for_prediction:
                    odds.append(int((-100) / (prediction - 1)))
                else:
                    odds.append(f"-{int((-100) / (prediction - 1)):.0f}")
        elif from_type == "percentage":
            if prediction == 0.5:
                if for_prediction:
                    odds.append(100)
                else:
                    odds.append("+100")
            if prediction < 0.5:
                if for_prediction:
                    odds.append(int(((1 - prediction) / prediction) * 100))
                else:
                    odds.append(f"+{((1 - prediction) / prediction) * 100:.0f}")
            else:
                if for_prediction:
                    odds.append(int((-100) / (prediction - 1)))
                else:
                    odds.append(f"-{int((-100) / (prediction - 1)):.0f}")

    return odds


def predict_fight(fighter1, fighter2, known_odds=False):

    if known_odds:
        odds = get_odds(fighter1, fighter2)
        if odds[0] != None and odds[1] != None:
            current_script_dir = os.path.dirname(__file__)
            scaler_relative_path = os.path.join(current_script_dir, "..", "Models", "Known_Odds", "scaler.pkl")
            scaler, saved_order = joblib.load(scaler_relative_path)
        else:
            print("No odds found. Using unknown odds.")
            known_odds = False

    if not known_odds:
        current_script_dir = os.path.dirname(__file__)
        scaler_relative_path = os.path.join(current_script_dir, "..", "Models", "Unknown_Odds", "scaler.pkl")
        scaler, saved_order = joblib.load(scaler_relative_path)
    
    df = two_fighter_stats(fighter1, fighter2)

    # Add odd values if known_odds
    if known_odds:
        print(odds)
        converted_odds = odds_conversion(odds, from_type="decimal", for_prediction=True)
        print(converted_odds)
        df["RedOdds"] = converted_odds[0]
        df["BlueOdds"] = converted_odds[1]
    

    # .copy() to maintain column order
    X_pred = df[saved_order].copy()
    # Use loaded scaler based on known_odds
    X_scaled = scaler.transform(X_pred)

    outcome_predictions_list = []
    winner_predictions_list = []

    # For each of the 6 models, load the model and make predictions
    # Allows us to ensemble the models for better accuracy
    for i in range(6):
        outcome_model = build_model(input_size=X_scaled.shape[1], output_size=6)
        winner_model = build_model(input_size=X_scaled.shape[1], output_size=2)
        if known_odds:
            current_script_dir = os.path.dirname(__file__)
            outcome_model_relative_path = os.path.join(current_script_dir, "..", "Models", "Known_Odds", f"ufc_model_{i}.pth")
            winner_model_relative_path = os.path.join(current_script_dir, "..", "Models", "Predicting_Winner_Odds", f"ufc_model_{i}.pth")
            outcome_model.load_state_dict(torch.load(outcome_model_relative_path, map_location=torch.device("cpu")))
            winner_model.load_state_dict(torch.load(winner_model_relative_path, map_location=torch.device("cpu")))
        else:
            current_script_dir = os.path.dirname(__file__)
            outcome_model_relative_path = os.path.join(current_script_dir, "..", "Models", "Unknown_Odds", f"ufc_model_{i}.pth")
            winner_model_relative_path = os.path.join(current_script_dir, "..", "Models", "Predicting_Winner", f"ufc_model_{i}.pth")
            outcome_model.load_state_dict(torch.load(outcome_model_relative_path, map_location=torch.device("cpu")))
            winner_model.load_state_dict(torch.load(winner_model_relative_path, map_location=torch.device("cpu")))
        outcome_model.eval()
        winner_model.eval()

        outcome_predictions = predict(outcome_model, X_scaled)[0]
        winner_predictions = predict(winner_model, X_scaled)[0]
        outcome_predictions_list.append(outcome_predictions)
        winner_predictions_list.append(winner_predictions)

    mean_outcome_pred = np.mean(np.stack(outcome_predictions_list), axis=0)
    mean_winner_pred = np.mean(np.stack(winner_predictions_list), axis=0)
    outcome_odds = odds_conversion(mean_outcome_pred, from_type="percentage", for_prediction=False)
    winner_odds = odds_conversion(mean_winner_pred, from_type="percentage", for_prediction=False)

    return mean_outcome_pred, mean_winner_pred, outcome_odds, winner_odds, known_odds

    


def predictions():
    
    # Get and validate fighter names
    print("Enter the first fighter: ")
    fighter1 = input()
    while not check_valid_fighter(fighter1): 
        print("Invalid fighter. Please try again.")
        fighter1 = input()

    print("Enter the second fighter: ")
    fighter2 = input()
    while not check_valid_fighter(fighter2):
        print("Invalid fighter. Please try again.")
        fighter2 = input()

    known_odds = False
    print("Do you want to use known odds? (y/n)")
    if input() == "y":
        known_odds = True

    mean_outcome_pred, mean_winner_pred, outcome_odds, winner_odds, odds_available = predict_fight(fighter1, fighter2, known_odds)


    if odds_available:
        print("Using Vegas Odds:")
    else:
        print("Using Unknown Odds:")
    print(f"\n\nPrediction: {fighter1} vs {fighter2}\n")
    print(f"\tRed Wins:   {mean_winner_pred[0]*100:.1f}% ({winner_odds[0]})")
    print(f"\tBlue Wins:  {mean_winner_pred[1]*100:.1f}% ({winner_odds[1]})")
    print(f"\tRed KO:   {mean_outcome_pred[0]*100:.1f}% ({outcome_odds[0]})")
    print(f"\tRed Sub:  {mean_outcome_pred[1]*100:.1f}% ({outcome_odds[1]})")
    print(f"\tRed Dec:  {mean_outcome_pred[2]*100:.1f}% ({outcome_odds[2]})")
    print(f"\tBlue KO:  {mean_outcome_pred[3]*100:.1f}% ({outcome_odds[3]})")
    print(f"\tBlue Sub: {mean_outcome_pred[4]*100:.1f}% ({outcome_odds[4]})")
    print(f"\tBlue Dec: {mean_outcome_pred[5]*100:.1f}% ({outcome_odds[5]})")
    print("\n")
    



if __name__ == "__main__":
    predictions()

    



