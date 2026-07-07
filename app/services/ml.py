"""
XGBoost-based fraud scoring.

The model is trained OFFLINE (see training/train_model.py) and loaded
once at API startup — never retrained per-request, that would be slow
and would leak training concerns into the request path.
"""

import os
from typing import Any
from app.services.features import build_features

try:
    import xgboost as xgb
except ModuleNotFoundError:  # pragma: no cover - exercised only when the driver is absent locally
    xgb = None

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "fraud_model.json")
MODEL_VERSION = "v1.0.0"

_model = None  # lazy-loaded singleton


def get_model() -> Any:
    global _model
    if xgb is None:
        raise RuntimeError("xgboost is not installed. Install requirements.txt to use ML scoring.")
    if _model is None:
        model = xgb.XGBClassifier()
        model.load_model(MODEL_PATH)
        _model = model
    return _model


def ml_score(data: dict) -> float:
    if xgb is None:
        raise RuntimeError("xgboost is not installed. Install requirements.txt to use ML scoring.")
    model = get_model()
    X = build_features(data)
    proba = model.predict_proba(X)[0][1]  # probability of class "1" = fraud
    return float(proba)
