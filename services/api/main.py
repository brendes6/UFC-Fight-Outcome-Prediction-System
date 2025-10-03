from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.api.app_util import two_fighter_stats
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware
import os
import joblib
import google.cloud.aiplatform





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
    try:
        stats = two_fighter_stats(fighter1, fighter2)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scaler_path = os.path.join(current_dir, "scaler.pkl")
    scaler, saved_order = joblib.load(scaler_path)
    

    X_pred = stats[saved_order].copy()
    X_scaled = scaler.transform(X_pred)
    features = X_scaled.tolist()


    project = "ufc-proj"
    endpoint_id = "8780500847814508544"
    location = "us-central1"
    api_endpoint = "us-central1-aiplatform.googleapis.com"

    client_options = {"api_endpoint": api_endpoint}
    client = google.cloud.aiplatform.gapic.PredictionServiceClient(client_options=client_options)
    
    endpoint = client.endpoint_path(
        project=project, location=location, endpoint=endpoint_id
    )
    
    response = client.predict(endpoint=endpoint, instances=features)

    # Extract the data into a standard Python list of dictionaries
    prediction_proto = response.predictions[0]

    predictions = list(prediction_proto['predictions'][0])


    # Return a dictionary containing only pure Python types
    return {"status": "success", "predictions": predictions}


