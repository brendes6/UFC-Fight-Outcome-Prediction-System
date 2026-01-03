from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app_util import two_fighter_stats_df
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware
import os
import joblib
import requests
import time

# Load in Huggingface API token
HF_API_TOKEN = os.getenv("HF_API_TOKEN")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionResponse(BaseModel):
    predicted_probs: Dict[str, float]
    value_picks: List[str]


@app.get("/")
def read_root():
    return {"message": "UFC API is live!"}

@app.get("/predict")
def predict(fighter1: str, fighter2: str):

    # Get fighter stats, catching errors for missing fighters
    try:
        stats = two_fighter_stats_df(fighter1, fighter2)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Load in scaler to scale fighter stats
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scaler_path = os.path.join(current_dir, "scaler.pkl")
    scaler, saved_order = joblib.load(scaler_path)
    
    X_pred = stats[saved_order].copy()
    print(X_pred.values.tolist())

    X_scaled = scaler.transform(X_pred)
    features = X_scaled.tolist()


    return {"status": "success", "features": X_pred.values.tolist()}

    # Initialize headers and payload for HF API request
    payload = {"inputs": features}
    headers = {}
    if HF_API_TOKEN:
        headers["Authorization"] = f"Bearer {HF_API_TOKEN}"

    headers["Content-Type"] =  "application/json"
    headers["Accept"] =  "application/json"

    # Retry HF API multiple times due to cold start times
    for i in range(3):

        response = requests.post(
            "https://df7w4xd6yu18jrhe.us-east-1.aws.endpoints.huggingface.cloud",
            headers=headers,
            json=payload,
        )

        if "error" in response.json():
            time.sleep(10)
        else:
            break

    # Extract predictions from response
    result = response.json()

    predictions = list(result[0]['predictions'][0])


    # Return a dictionary containing only pure Python types
    return {"status": "success", "predictions": predictions}


