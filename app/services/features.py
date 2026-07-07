"""
Feature engineering shared between offline training (training/train_model.py)
and online inference (app/services/ml.py).

Keeping this in one place guarantees the model always sees features
computed the exact same way it was trained on.
"""

from typing import Any

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - exercised only when the dependency is absent locally
    pd = None

FEATURE_COLUMNS = [
    "usage_ratio",
    "device_age_days",
    "num_devices_30d",
    "failed_payments_7d",
    "account_age_days",
    "is_odd_hour",
    "distance_from_usual_km",
]


def build_features(data: dict) -> Any:
    if pd is None:
        raise RuntimeError("pandas is not installed. Install requirements.txt to use ML scoring.")
    usage_ratio = data["usage_mb"] / data["avg_usage_mb"] if data["avg_usage_mb"] > 0 else 0.0
    is_odd_hour = 1 if data["login_hour"] <= 5 or data["login_hour"] >= 23 else 0

    row = {
        "usage_ratio": usage_ratio,
        "device_age_days": data["device_age_days"],
        "num_devices_30d": data["num_devices_30d"],
        "failed_payments_7d": data["failed_payments_7d"],
        "account_age_days": data["account_age_days"],
        "is_odd_hour": is_odd_hour,
        "distance_from_usual_km": data["distance_from_usual_km"],
    }
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)
