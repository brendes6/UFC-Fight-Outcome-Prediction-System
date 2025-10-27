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

    # Get fighter stats, catching errors for missing fighters
    try:
        stats = two_fighter_stats(fighter1, fighter2)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

    # As of Oct 27 '25 - The Vertex AI model was taken down due to high
    # deployment costs. We only allow for 4 specific cached entries now.
    combined = fighter1 + " " + fighter2
    
    predictions_cache = {
        "Merab Dvalishvili Umar Nurmagomedov": [0.1260437220335007,0.1847986578941345,0.3752331435680389,0.1175856217741966,0.05286609381437302,0.1434727013111115],
        "Alexandre Pantoja Joshua Van": [0.1149917095899582,0.06824878603219986,0.3165818750858307,0.196114256978035,0.06324214488267899,0.2408213019371033],
        "Alex Pereira Carlos Ulberg": [0.3269651830196381,0.03805437311530113,0.1599053293466568,0.1833450645208359,0.0786086693406105,0.2131213694810867],
        "Khamzat Chimaev Anthony Hernandez": [0.1912300586700439,0.1523086577653885,0.1884087771177292,0.1327592730522156,0.1377740651369095,0.1975191235542297]
    }

    if combined in predictions_cache:
        predictions = predictions_cache[combined]
        return {"status": "success", "predictions": predictions}

    raise HTTPException(status_code=404, detail="Unfortunately, the model deployment is shut down for cost purposes. Please try one of our cached predictions!")
    
    # Old code for handling vertex AI API calls

    # Load in our scaler to scale our fighter stats
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scaler_path = os.path.join(current_dir, "scaler.pkl")
    scaler, saved_order = joblib.load(scaler_path)
    
    X_pred = stats[saved_order].copy()
    X_scaled = scaler.transform(X_pred)
    features = X_scaled.tolist()
    
    # Call Vertex AI endpoint for predictions
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


