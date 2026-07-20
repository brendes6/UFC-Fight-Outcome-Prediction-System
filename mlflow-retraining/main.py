"""
main.py: weekly retraining pipeline.

Retrains the NN + XGBoost models, logs the ensembled accuracy to a persistent
MLFlow tracking stored backed by our Postgres DB and GCS artifacts. Registers the
trained ensemble as a new version of the "ufc-fight-predictor" model, and checks
if it beats current production accuracy via "champion", promoting it if so. Promotion
is done via the champion alias in MLFlow and the onnx models in GCS are updated.
"""

import json
from datetime import date

import numpy as np
import pandas as pd

import mlflow
from mlflow.tracking import MlflowClient

import mlflow_registry as registry
from augment import FINAL_FEATURES
from model_util import (
    load_data, clean_and_scale, train_model, train_xgboost,
    export_nn_to_onnx, export_xgb_to_onnx, evaluate_ensemble, ensemble_probs,
    scaler_to_metadata, get_current_version, update_production_accuracy_in_db,
)

EXPERIMENT = "ufc-predictor"
PROMOTION_MARGIN = 0.005  # candidate must beat the champion by this much to win


def onnx_serving_probs(nn_path, xgb_path, scaler_dict, raw):
    """Reproduce the production serving computation directly from the ONNX files.

    Independent of the registered pyfunc wrapper: scales raw features with the
    saved scaler, softmaxes the NN logits, averages with XGBoost probabilities.
    Used to prove the registered model == the artifacts synced to production.
    """
    import onnxruntime as ort

    order = scaler_dict["saved_order"]
    mean = np.array([scaler_dict["means"][n] for n in order], dtype=np.float32)
    std = np.array([scaler_dict["stds"][n] for n in order], dtype=np.float32)
    scaled = ((np.asarray(raw, dtype=np.float32) - mean) / std).astype(np.float32)

    nn = ort.InferenceSession(nn_path, providers=["CPUExecutionProvider"])
    xgb = ort.InferenceSession(xgb_path, providers=["CPUExecutionProvider"])
    logits = np.asarray(nn.run(None, {nn.get_inputs()[0].name: scaled})[0])
    z = logits - logits.max(axis=1, keepdims=True)
    e = np.exp(z)
    nn_p = e / e.sum(axis=1, keepdims=True)
    outs = xgb.run(None, {xgb.get_inputs()[0].name: scaled})
    xgb_p = next(
        (np.asarray(o, dtype=np.float32) for o in outs
         if np.asarray(o).ndim == 2 and np.asarray(o).shape[1] == 6),
        np.asarray(outs[-1], dtype=np.float32),
    )
    return (nn_p + xgb_p) / 2.0


# Point MLflow at the persistent store (Postgres + GCS in prod; local SQLite
# fallback for offline dev) and make sure the experiment exists.
tracking_uri = registry.configure_tracking(EXPERIMENT)
print(f"MLflow tracking: {tracking_uri}")

# Load and prepare data
data = load_data()
X_train, y_train, X_val, y_val, X_val_raw, scaler = clean_and_scale(data)

with mlflow.start_run(run_name=f"retrain_{date.today()}") as run:

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

    # Train both models
    print("=" * 60, "\nTraining Neural Network...\n", "=" * 60)
    nn_model, nn_val_loss = train_model(X_train, y_train, X_val, y_val)
    mlflow.log_metric("nn_val_loss", nn_val_loss)

    print("=" * 60, "\nTraining XGBoost...\n", "=" * 60)
    xgb_model, xgb_val_loss = train_xgboost(X_train, y_train, X_val, y_val)
    mlflow.log_metric("xgb_val_loss", xgb_val_loss)

    # Evaluate heterogeneous ensemble
    print("=" * 60, "\nEvaluating Ensemble (NN + XGBoost)...\n", "=" * 60)
    accuracy = evaluate_ensemble(nn_model, xgb_model, X_val, y_val)
    mlflow.log_metrics({
        "winner_accuracy": accuracy["winner"],
        "outcome_accuracy": accuracy["outcome"],
    })

    # Export models + scaler to ONNX/JSON (used for both artifacts + serving) ──
    nn_path, xgb_path = "nn_model.onnx", "xgb_model.onnx"
    export_nn_to_onnx(nn_model, nn_path)
    export_xgb_to_onnx(xgb_model, xgb_path)

    scaler_dict = scaler_to_metadata(scaler)
    scaler_path = "scaler_params.json"
    with open(scaler_path, "w") as f:
        json.dump(scaler_dict, f)

    # Register the ensemble as a new model version
    example = pd.DataFrame(X_val_raw[:2], columns=FINAL_FEATURES)
    version = registry.log_and_register(
        run.info.run_id, nn_path, xgb_path, scaler_path, accuracy,
        input_example=example,
    )
    print(f"Registered {registry.REGISTERED_MODEL} v{version.version}")

    # Parity check: the registered artifact must reproduce the served computation 

    # The pyfunc bundles the exact ONNX files that get synced to production/, so it
    # must match an independent recomputation from those files to numerical noise.
    # (We also record how far the ONNX ensemble drifts from the native trained
    # models, dominated by XGBoost's ONNX conversion, as an export-fidelity metric.)
    loaded = mlflow.pyfunc.load_model(f"runs:/{run.info.run_id}/{registry.ARTIFACT_PATH}")
    sample_raw = X_val_raw[:64]
    pyfunc_probs = np.asarray(loaded.predict(pd.DataFrame(sample_raw, columns=FINAL_FEATURES)))
    serving_probs = onnx_serving_probs(nn_path, xgb_path, scaler_dict, sample_raw)
    native_probs = ensemble_probs(nn_model, xgb_model, scaler.transform(sample_raw))

    serving_diff = float(np.max(np.abs(pyfunc_probs - serving_probs)))
    native_diff = float(np.max(np.abs(serving_probs - native_probs)))
    mlflow.log_metric("registry_serving_parity_max_abs_diff", serving_diff)
    mlflow.log_metric("onnx_vs_native_max_abs_diff", native_diff)
    print(f"Registry vs serving parity max |Δ|: {serving_diff:.2e}  "
          f"(ONNX vs native export drift: {native_diff:.2e})")
    if serving_diff > 1e-5:
        raise RuntimeError(f"Registered model diverges from the served ONNX artifacts ({serving_diff:.2e})")

    # Registry-gated promotion
    client = MlflowClient()
    champion_acc = registry.get_champion_accuracy(client)

    if accuracy["winner"] > champion_acc + PROMOTION_MARGIN:
        next_version = get_current_version() + 1
        registry.promote(
            client, version.version, accuracy,
            nn_path, xgb_path, scaler_dict, next_version,
        )
        update_production_accuracy_in_db(accuracy["winner"], next_version)
        mlflow.set_tag("promoted", "true")
        mlflow.set_tag("champion_version", version.version)
        print(f"Promoted to champion: {champion_acc:.3f} → {accuracy['winner']:.3f} "
              f"(serving v{next_version})")
    else:
        mlflow.set_tag("promoted", "false")
        print(f"No promotion: {accuracy['winner']:.3f} didn't beat "
              f"champion {champion_acc:.3f} + {PROMOTION_MARGIN}")
