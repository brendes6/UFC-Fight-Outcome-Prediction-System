"""
ensemble_model.py: Modular tool allowing MLflow to register 'models from code'

This module is used to define the UFCEnsemble model for MLflow. The model loads
the pre-trained ONNX models and the StandardScaler metadata. It provides
methods for loading the model context and making predictions, making the artifact
independently loadable and usable by MLFlow.
"""

import json

import numpy as np

import mlflow


def _softmax(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def _xgb_probs(outputs) -> np.ndarray:
    """Pick the [N, 6] probability tensor out of the XGBoost ONNX outputs.

    onnxmltools emits [label, probabilities]; with zipmap disabled the second
    output is a plain float tensor, but we match by shape to be robust.
    """
    for out in outputs:
        arr = np.asarray(out)
        if arr.ndim == 2 and arr.shape[1] == 6:
            return arr.astype(np.float32)
        
    # Fallback: last output, coerced to 2-D.
    arr = np.asarray(outputs[-1], dtype=np.float32)
    return arr.reshape(len(arr), -1)


class UFCEnsemble(mlflow.pyfunc.PythonModel):
    """Loadable NN + XGBoost ensemble with the StandardScaler baked in.

    Input: raw (unscaled) feature rows in saved_order (DataFrame or ndarray).
    Output: [N, 6] averaged class probabilities, matching the Go backend.
    """

    def load_context(self, context):
        import onnxruntime as ort

        providers = ["CPUExecutionProvider"]
        self._nn = ort.InferenceSession(context.artifacts["nn_onnx"], providers=providers)
        self._xgb = ort.InferenceSession(context.artifacts["xgb_onnx"], providers=providers)
        with open(context.artifacts["scaler"]) as f:
            meta = json.load(f)
        order = meta["saved_order"]
        self._order = order
        self._mean = np.array([meta["means"][name] for name in order], dtype=np.float32)
        self._std = np.array([meta["stds"][name] for name in order], dtype=np.float32)
        self._nn_input = self._nn.get_inputs()[0].name
        self._xgb_input = self._xgb.get_inputs()[0].name

    def _to_array(self, model_input) -> np.ndarray:
        if hasattr(model_input, "to_numpy"):
            model_input = model_input.to_numpy()
        return np.asarray(model_input, dtype=np.float32)

    def predict(self, context, model_input):
        raw = self._to_array(model_input)
        scaled = ((raw - self._mean) / self._std).astype(np.float32)
        nn_prob = _softmax(np.asarray(self._nn.run(None, {self._nn_input: scaled})[0]))
        xgb_prob = _xgb_probs(self._xgb.run(None, {self._xgb_input: scaled}))
        return (nn_prob + xgb_prob) / 2.0


mlflow.models.set_model(UFCEnsemble())
