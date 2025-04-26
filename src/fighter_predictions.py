import pandas as pd
import numpy as np
import torch
from fighter_diffs import two_fighter_stats
from feature_engineering import get_X_y
import joblib
from model import predict, build_model
from fighter_diffs import check_valid_fighter

def odds_conversion(predictions):
    # Convert percentage predictions to odds
    odds = []
    for prediction in predictions:
        if prediction == 0.5:
            odds.apend("+100")
        if prediction < 0.5:
            odds.append(f"+{((1 - prediction) / prediction) * 100:.0f}")
        else:
            odds.append(f"{-prediction / (1 - prediction) * 100:.0f}")
    return odds


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
        print("Enter Red Odds:")
        red_odds = float(input())
        print("Enter the odds for a Red KO: ")
        red_ko = float(input())
        print("Enter the odds for a Red Sub: ")
        red_sub = float(input())
        print("Enter the odds for a Red Dec: ")
        red_dec = float(input())

        print("Enter Blue Odds:")
        blue_odds = float(input())
        print("Enter the odds for a Blue KO: ")
        blue_ko = float(input())
        print("Enter the odds for a Blue Sub: ")
        blue_sub = float(input())
        print("Enter the odds for a Blue Dec: ")
        blue_dec = float(input())
        scaler, saved_order = joblib.load("../Models/Known_Odds/scaler.pkl")
    else:
        scaler, saved_order = joblib.load("../Models/Unknown_Odds/scaler.pkl")
    

    df = two_fighter_stats(fighter1, fighter2)

    # Add odd values if known_odds
    if known_odds:
        df["RedOdds"] = red_odds
        df["BlueOdds"] = blue_odds
        df["RedDecOdds"] = red_dec
        df["BlueDecOdds"] = blue_dec
        df["RSubOdds"] = red_sub
        df["BSubOdds"] = blue_sub   
        df["RKOOdds"] = red_ko
        df["BKOOdds"] = blue_ko
    

    # .copy() to maintain column order
    X_pred = df[saved_order].copy()
    # Use loaded scaler based on known_odds
    X_scaled = scaler.transform(X_pred)

    predictions_list = []

    # For each of the 6 models, load the model and make predictions
    # Allows us to ensemble the models for better accuracy
    for i in range(6):
        model = build_model(input_size=X_scaled.shape[1], output_size=6)
        if known_odds:
            model.load_state_dict(torch.load(f"../Models/Known_Odds/ufc_model_{i}.pth", map_location=torch.device("cpu")))
        else:
            model.load_state_dict(torch.load(f"../Models/Unknown_Odds/ufc_model_{i}.pth", map_location=torch.device("cpu")))
        model.eval()

        predictions = predict(model, X_scaled)
        prediction = predictions[0] 
        predictions_list.append(prediction)

    mean_pred = np.mean(np.stack(predictions_list), axis=0)

    odds = odds_conversion(mean_pred)

    print(f"\n\nPrediction: {fighter1} vs {fighter2}\n")
    print(f"\tRed KO:   {mean_pred[0]*100:.1f}% ({odds[0]})")
    print(f"\tRed Sub:  {mean_pred[1]*100:.1f}% ({odds[1]})")
    print(f"\tRed Dec:  {mean_pred[2]*100:.1f}% ({odds[2]})")
    print(f"\tBlue KO:  {mean_pred[3]*100:.1f}% ({odds[3]})")
    print(f"\tBlue Sub: {mean_pred[4]*100:.1f}% ({odds[4]})")
    print(f"\tBlue Dec: {mean_pred[5]*100:.1f}% ({odds[5]})")
    print("\n")



if __name__ == "__main__":
    predictions()

    



