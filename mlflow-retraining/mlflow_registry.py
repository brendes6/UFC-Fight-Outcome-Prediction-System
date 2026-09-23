"""
MLFlow model registry integration for the retraining pipeline.

This module provides helpers to allow the retraining pipeline to log
persistent MLflow tracking information and manage model registration. Retraining
logs are stored in the Postgres backend and model artifacts are stored on
the GCS bucket for the Go backend to pull from.

Design:
- One registered model (ufc-fight-predictor) so that each retraining targets updating this
- The model is a pyfunc model (MLFlow model format allowing code/models to be deployed
as a standard python function) that handles bundling the NN/XGBoost model for inference 
along with the scaler.
- The registry provides a source of truth for which model is live, and GCS stores
that artifact for the Go backend to pull in.
"""

import json
import os

import mlflow
from mlflow.tracking import MlflowClient
import pit_features

REGISTERED_MODEL = os.environ.get("MLFLOW_REGISTERED_MODEL", "ufc-fight-predictor")
CHAMPION_ALIAS = "champion"
ARTIFACT_PATH = "ensemble"
MODEL_CODE_PATH = os.path.join(os.path.dirname(__file__), "ensemble_model.py")

SERVING_BUCKET = os.environ.get("SERVING_BUCKET", "ufc-proj-models")
SERVING_PREFIX = os.environ.get("SERVING_PREFIX", "production")
FEATURE_VERSION = pit_features.FEATURE_VERSION


# Tracking setup
def configure_tracking(experiment_name: str):
    """Point MLflow at the persistent store and ensure the experiment exists.

    Reads MLFLOW_TRACKING_URI (Postgres in prod; falls back to a local
    SQLite file for offline dev) and MLFLOW_ARTIFACT_ROOT (a gs:// path
    in prod). The artifact root is bound to the experiment on first creation.
    """
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    artifact_root = os.environ.get("MLFLOW_ARTIFACT_ROOT")
    mlflow.set_tracking_uri(tracking_uri)

    exp = mlflow.get_experiment_by_name(experiment_name)
    if exp is None:
        mlflow.create_experiment(experiment_name, artifact_location=artifact_root)
    mlflow.set_experiment(experiment_name)
    return tracking_uri


# Registration + promotion
def log_and_register(run_id, nn_onnx_path, xgb_onnx_path, scaler_path, accuracy,
                     input_example=None):
    """Log the ensemble as a pyfunc model and register a new model version.

    Returns the created ModelVersion. The winner/outcome accuracies are
    stored as version tags so promotion decisions never need a second source.
    """
    artifacts = {
        "nn_onnx": nn_onnx_path,
        "xgb_onnx": xgb_onnx_path,
        "scaler": scaler_path,
    }
    mlflow.pyfunc.log_model(
        artifact_path=ARTIFACT_PATH,
        python_model=MODEL_CODE_PATH,
        artifacts=artifacts,
        input_example=input_example,
        pip_requirements=["onnxruntime", "numpy"],
    )

    model_uri = f"runs:/{run_id}/{ARTIFACT_PATH}"
    version = mlflow.register_model(model_uri, REGISTERED_MODEL)

    client = MlflowClient()
    client.set_model_version_tag(REGISTERED_MODEL, version.version,
                                 "winner_accuracy", f"{accuracy['winner']:.6f}")
    client.set_model_version_tag(REGISTERED_MODEL, version.version,
                                 "outcome_accuracy", f"{accuracy['outcome']:.6f}")
    client.set_model_version_tag(REGISTERED_MODEL, version.version,
                                 "feature_version", FEATURE_VERSION)
    return version


def get_champion_accuracy(client: MlflowClient) -> float:
    """Winner accuracy of the current champion, or 0.0 if there is none yet."""
    try:
        mv = client.get_model_version_by_alias(REGISTERED_MODEL, CHAMPION_ALIAS)
    except Exception:
        return 0.0
    return float(mv.tags.get("winner_accuracy", 0.0))


def promote(client: MlflowClient, version: str, accuracy: dict,
            nn_onnx_path: str, xgb_onnx_path: str, scaler_dict: dict,
            model_version_number: int):
    """Make ``version`` the champion and sync its artifacts to the serving path."""
    client.set_registered_model_alias(REGISTERED_MODEL, CHAMPION_ALIAS, version)
    sync_to_serving(nn_onnx_path, xgb_onnx_path, scaler_dict,
                    model_version_number, accuracy["winner"])


def sync_to_serving(nn_onnx_path, xgb_onnx_path, scaler_dict, version, winner_accuracy):
    """Copy the champion's ONNX models + scaler to gs://<bucket>/production/.

    This is the serving contract the Go backend reads at startup. Files are
    already exported locally by the training run, so this is a pure upload.
    """
    from datetime import date

    from google.cloud import storage

    bucket = storage.Client().bucket(SERVING_BUCKET)
    bucket.blob(f"{SERVING_PREFIX}/nn_model.onnx").upload_from_filename(nn_onnx_path)
    bucket.blob(f"{SERVING_PREFIX}/xgb_model.onnx").upload_from_filename(xgb_onnx_path)
    bucket.blob(f"{SERVING_PREFIX}/scaler_params.json").upload_from_string(
        json.dumps(scaler_dict)
    )
    bucket.blob(f"{SERVING_PREFIX}/version.json").upload_from_string(
        json.dumps({
            "version": version,
            "winner_accuracy": winner_accuracy,
            "feature_version": scaler_dict.get("feature_version", FEATURE_VERSION),
            "trained_at": str(date.today()),
        })
    )
