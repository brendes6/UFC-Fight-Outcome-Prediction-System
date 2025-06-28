from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app_util import check_valid_fighter, get_odds_data, get_value_picks
from fighter_predictions import predict_fight
from typing import Dict, List

app = FastAPI()


class PredictionResponse(BaseModel):
    predicted_probs: Dict[str, float]
    value_picks: List[str]


@app.get("/")
def read_root():
    return {"message": "UFC API is live!"}

@app.get("/predict")
def predict(fighter1: str, fighter2: str):
    valid = check_valid_fighter(fighter1, fighter2)

    if valid == "":
        odds_data = get_odds_data(fighter1, fighter2)
        if any(i==None for i in odds_data.values()):
            picks = ["No value picks available."]
            mean_outcome_pred, mean_winner_pred, _, _ = predict_fight(fighter1, fighter2, odds_data=None)
        else:
            mean_outcome_pred, mean_winner_pred, _, _ = predict_fight(fighter1, fighter2, odds_data=odds_data)
            picks = get_value_picks(odds_data, mean_outcome_pred, mean_winner_pred)
        
        response = {
                "predicted_probs": {
                    "Red to Win": float(mean_winner_pred[0]),
                    "Blue to Win": float(mean_winner_pred[1]),
                    "Red by KO": float(mean_outcome_pred[0]),
                    "Red by Sub": float(mean_outcome_pred[1]),
                    "Red by Dec": float(mean_outcome_pred[2]),
                    "Blue by KO": float(mean_outcome_pred[3]),
                    "Blue by Sub": float(mean_outcome_pred[4]),
                    "Blue by Dec": float(mean_outcome_pred[5])
                },
                "value_picks": picks
                }
        
        return response

    
    else:
        raise HTTPException(status_code=404, detail=f"Error: {valid} is not a valid fighter")
