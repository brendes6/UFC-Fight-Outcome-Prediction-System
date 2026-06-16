"""
main.py - script to run full mlflow pipeline for retraining,
model accuracy tracking, versioning and model promotion
"""

import mlflow
from datetime import date
import json
from model_util import (load_data, clean_and_scale, train_model, export_to_onnx, 
    evaluate_ensemble, get_production_accuracy_from_db, promote_to_production)

# Write logs to local sqlite db
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("ufc-predictor")

# Load and clean data
data = load_data()
X_train, y_train, X_val, y_val, scaler = clean_and_scale(data)

# Start MLFlow run for this training session
with mlflow.start_run(run_name=f"retrain_{date.today()}"):
    
    # Log hyperparameters
    mlflow.log_params({
        "training_samples": len(X_train),
        "num_features": X_train.shape[1],
        "training_date": str(date.today()),
        "learning_rate": 0.0005,
        "batch_size": 64,
        "weight_decay": 0.01,
        "label_smoothing": 0.1,
        "num_epochs_max": 500,
        "early_stopping_patience": 15,
        "ensemble_size": 4
    })
    
    # Train 4 models for us to ensemble
    results = [train_model(X_train, y_train, X_val, y_val) for _ in range(4)]
    models = [r[0] for r in results]
    
    # Log individual model validation losses
    for i, (_, val_loss) in enumerate(results):
        mlflow.log_metric(f"model_{i}_val_loss", val_loss)
    
    # Evaluate ensemble
    accuracy = evaluate_ensemble(models, X_val, y_val)
    
    # Log metrics
    mlflow.log_metrics({
        "winner_accuracy": accuracy["winner"],
        "outcome_accuracy": accuracy["outcome"]
    })
    
    # Export to ONNX and log as artifacts
    for i, model in enumerate(models):
        path = f"model_{i}.onnx"
        export_to_onnx(model, path)
        mlflow.log_artifact(path)
    
    # Serialize scaler params and log as artifact
    scaler_dict = {
        "means": scaler.mean_.tolist(),
        "stds": scaler.scale_.tolist()
    }
    with open("scaler_params.json", "w") as f:
        json.dump(scaler_dict, f)
    mlflow.log_artifact("scaler_params.json")
    
    # Get current production accuracy from Firestore
    current_accuracy = get_production_accuracy_from_db()
    
    # Promote if better
    if accuracy["winner"] > current_accuracy + 0.005:
        promote_to_production(models, scaler, accuracy)
        mlflow.set_tag("promoted", "true")
        print(f"Promoted: {current_accuracy:.3f} → {accuracy['winner']:.3f}")
    else:
        mlflow.set_tag("promoted", "false")
        print(f"No promotion: {accuracy['winner']:.3f} didn't beat {current_accuracy:.3f}")