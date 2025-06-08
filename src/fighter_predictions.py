import numpy as np
import torch
from app_util import two_fighter_stats
import joblib
from model import predict, build_model
import os
import streamlit as st
from app_util import odds_conversion

@st.cache_resource
def predict_fight(fighter1, fighter2, odds_data=None):

    # Check if odds data is provided
    if odds_data != None:
        current_script_dir = os.path.dirname(__file__)
        scaler_relative_path = os.path.join(current_script_dir, "..", "Models", "Known_Odds", "scaler.pkl")
        scaler, saved_order = joblib.load(scaler_relative_path)
        known_odds = True
    else:
        known_odds = False

    # If odds data is not provided, use unknown odds
    if not known_odds:
        current_script_dir = os.path.dirname(__file__)
        scaler_relative_path = os.path.join(current_script_dir, "..", "Models", "Unknown_Odds", "scaler.pkl")
        scaler, saved_order = joblib.load(scaler_relative_path)
    
    df = two_fighter_stats(fighter1, fighter2)

    # Add odd values if known_odds
    if known_odds:
        df["RedOdds"] = int(odds_data["RedOdds"])
        df["BlueOdds"] = int(odds_data["BlueOdds"])

    

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
    outcome_odds = odds_conversion(mean_outcome_pred)
    winner_odds = odds_conversion(mean_winner_pred)

    mean_outcome_pred = [
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
        mean_outcome_pred[2] + mean_outcome_pred[5],
    ]

    return mean_outcome_pred, mean_winner_pred, outcome_odds, winner_odds

    


    



