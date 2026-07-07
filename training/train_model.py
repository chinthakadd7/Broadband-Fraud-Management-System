"""
Offline training script for the XGBoost fraud model.

Run this separately from the API (`python training/train_model.py`).
It writes app/models/fraud_model.json, which the API loads at startup.

NOTE: This script generates SYNTHETIC data so the project runs end-to-end
out of the box. Replace `generate_synthetic_data()` with a loader that
pulls your real, labeled historical fraud data before using this for
anything real.
"""

import os
import sys
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.services.features import FEATURE_COLUMNS

MODEL_OUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "app", "models", "fraud_model.json"
)
DATASET_PATH = os.path.join(os.path.dirname(__file__), "synthetic_broadband_fraud_data.csv")


def load_dataset() -> pd.DataFrame:
    if os.path.exists(DATASET_PATH):
        return pd.read_csv(DATASET_PATH)

    from generate_synthetic_dataset import generate_broadband_synthetic_data
    df = generate_broadband_synthetic_data()
    df.to_csv(DATASET_PATH, index=False)
    return df


def train():
    print("Loading synthetic training data...")
    df = load_dataset()

    df = df.copy()
    df["usage_ratio"] = df["usage_mb"] / df["avg_usage_mb"].replace(0, np.nan)
    df["usage_ratio"] = df["usage_ratio"].fillna(0.0)
    df["is_odd_hour"] = ((df["login_hour"] <= 5) | (df["login_hour"] >= 23)).astype(int)

    X = df[FEATURE_COLUMNS]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Fraud is rare -> tell XGBoost to weight the minority class more heavily
    neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
    scale_pos_weight = neg / pos

    print(f"Training on {len(X_train)} rows (fraud rate={y_train.mean():.3f}), "
          f"scale_pos_weight={scale_pos_weight:.2f}")

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    print("\n--- Evaluation on held-out test set ---")
    print(classification_report(y_test, y_pred, target_names=["legit", "fraud"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

    os.makedirs(os.path.dirname(MODEL_OUT_PATH), exist_ok=True)
    model.save_model(MODEL_OUT_PATH)
    print(f"\nModel saved to {MODEL_OUT_PATH}")


if __name__ == "__main__":
    train()
