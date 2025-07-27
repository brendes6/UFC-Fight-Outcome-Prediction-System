import numpy as np
import torch
from app_util import two_fighter_stats
import joblib
from model import predict, build_model
import os
from app_util import odds_conversion


def predict_fight(fighter1, fighter2):

    # Load in scaler
    current_script_dir = os.path.dirname(__file__)
    scaler_relative_path = os.path.join(current_script_dir, "Models", "Unknown_Odds", "scaler.pkl")
    scaler, saved_order = joblib.load(scaler_relative_path)
    
    df = two_fighter_stats(fighter1, fighter2)
    

    # .copy() to maintain column order
    X_pred = df[saved_order].copy()
    # Use loaded scaler based on known_odds
    X_scaled = scaler.transform(X_pred)

    # Build models
    outcome_model = build_model(input_size=X_scaled.shape[1], output_size=6)
    winner_model = build_model(input_size=X_scaled.shape[1], output_size=2)

    # Load model weights
    current_script_dir = os.path.dirname(__file__)
    outcome_model_relative_path = os.path.join(current_script_dir, "Models", "Unknown_Odds", f"ufc_model_0.pth")
    winner_model_relative_path = os.path.join(current_script_dir, "Models", "Predicting_Winner", f"ufc_model_0.pth")
    outcome_model.load_state_dict(torch.load(outcome_model_relative_path, map_location=torch.device("cpu")))
    winner_model.load_state_dict(torch.load(winner_model_relative_path, map_location=torch.device("cpu")))


    # Set models to evaluation mode
    outcome_model.eval()
    winner_model.eval()

    # Make predictions
    outcome_predictions = predict(outcome_model, X_scaled)[0]
    winner_predictions = predict(winner_model, X_scaled)[0]

    outcome_odds = odds_conversion(outcome_predictions)
    winner_odds = odds_conversion(winner_predictions)


    return outcome_predictions, winner_predictions, outcome_odds, winner_odds

    


    



