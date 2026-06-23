"""
main.py - script to run full mlflow pipeline for retraining,
model accuracy tracking, versioning and model promotion
"""

import mlflow
from datetime import date
import json
from model_util import (load_data, clean_and_scale, train_model, train_xgboost,
    export_nn_to_onnx, export_xgb_to_onnx, evaluate_ensemble,
    get_production_accuracy_from_db, promote_to_production)

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
        "validation_samples": len(X_val),
        "num_features": X_train.shape[1],
        "training_date": str(date.today()),
        "split_type": "temporal",
        "augmentation": "red_blue_swap",
        "ensemble_type": "nn+xgboost",
        # NN params
        "nn_learning_rate": 0.0005,
        "nn_batch_size": 64,
        "nn_weight_decay": 0.01,
        "nn_label_smoothing": 0.1,
        "nn_max_epochs": 500,
        "nn_early_stopping_patience": 15,
        # XGBoost params
        "xgb_n_estimators": 400,
        "xgb_max_depth": 6,
        "xgb_learning_rate": 0.05,
        "xgb_subsample": 0.8,
        "xgb_early_stopping_rounds": 20,
    })
    
    # ── Train both models ──
    print("=" * 60)
    print("Training Neural Network...")
    print("=" * 60)
    nn_model, nn_val_loss = train_model(X_train, y_train, X_val, y_val)
    mlflow.log_metric("nn_val_loss", nn_val_loss)
    
    print("\n" + "=" * 60)
    print("Training XGBoost...")
    print("=" * 60)
    xgb_model, xgb_val_loss = train_xgboost(X_train, y_train, X_val, y_val)
    mlflow.log_metric("xgb_val_loss", xgb_val_loss)
    
    # ── Evaluate heterogeneous ensemble ──
    print("\n" + "=" * 60)
    print("Evaluating Ensemble (NN + XGBoost)...")
    print("=" * 60)
    accuracy = evaluate_ensemble(nn_model, xgb_model, X_val, y_val)
    
    # Log metrics
    mlflow.log_metrics({
        "winner_accuracy": accuracy["winner"],
        "outcome_accuracy": accuracy["outcome"]
    })
    
    # ── Export models to ONNX and log as artifacts ──
    nn_path = "nn_model.onnx"
    export_nn_to_onnx(nn_model, nn_path)
    mlflow.log_artifact(nn_path)

    xgb_path = "xgb_model.onnx"
    export_xgb_to_onnx(xgb_model, xgb_path)
    mlflow.log_artifact(xgb_path)
    
    # Serialize scaler params and log as artifact
    scaler_dict = {
        "means": scaler.mean_.tolist(),
        "stds": scaler.scale_.tolist()
    }
    with open("scaler_params.json", "w") as f:
        json.dump(scaler_dict, f)
    mlflow.log_artifact("scaler_params.json")
    
    # ── Promote if better than current production ──
    current_accuracy = get_production_accuracy_from_db()
    
    if accuracy["winner"] > current_accuracy + 0.005:
        promote_to_production(nn_model, xgb_model, scaler, accuracy)
        mlflow.set_tag("promoted", "true")
        print(f"\nPromoted: {current_accuracy:.3f} → {accuracy['winner']:.3f}")
    else:
        mlflow.set_tag("promoted", "false")
        print(f"\nNo promotion: {accuracy['winner']:.3f} didn't beat {current_accuracy:.3f}")