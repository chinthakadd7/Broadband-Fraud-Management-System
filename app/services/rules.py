"""
Rule-based fraud scoring.

This layer encodes domain-expert knowledge as simple, fast, fully
explainable if-else checks. It requires no training data and can be
tuned live by editing app/config/rules.yaml — no redeploy needed
(the config is reloaded on every import of this module via load_rules()).
"""

import os
from typing import Tuple, List, Dict

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only when the dependency is absent locally
    yaml = None

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "rules.yaml")


def load_rules() -> Dict:
    if yaml is None:
        raise RuntimeError("pyyaml is not installed. Install requirements.txt to use rule scoring.")
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def rule_based_score(data: dict) -> Tuple[float, List[str], bool]:
    """
    Returns:
        normalized_score: float in [0, 1]
        triggered: list of rule names that fired
        hard_block: True if a hard rule (e.g. blacklisted MAC) fired,
                    meaning the ensemble should be bypassed entirely.
    """
    cfg = load_rules()
    score = 0
    triggered: List[str] = []
    hard_block = False

    # Hard rule: blacklisted device
    if data["mac_address"] in cfg.get("blacklisted_macs", []):
        triggered.append("blacklisted_device")
        hard_block = True

    # Usage spike vs personal average
    r = cfg["usage_spike"]
    if data["avg_usage_mb"] > 0 and data["usage_mb"] > r["multiplier"] * data["avg_usage_mb"]:
        score += r["points"]
        triggered.append("usage_spike")

    # New device + high usage (possible SIM swap / device fraud)
    r = cfg["new_device_high_usage"]
    if data["device_age_days"] <= r["max_device_age_days"] and data["usage_mb"] >= r["min_usage_mb"]:
        score += r["points"]
        triggered.append("new_device_high_usage")

    # Odd-hour login from an unusual location
    r = cfg["odd_hour_new_location"]
    if (r["start_hour"] <= data["login_hour"] <= r["end_hour"]
            and data["distance_from_usual_km"] >= r["min_distance_km"]):
        score += r["points"]
        triggered.append("odd_hour_new_location")

    # Repeated failed payments (billing fraud / stolen card testing)
    r = cfg["payment_failures"]
    if data["failed_payments_7d"] >= r["min_failures_7d"]:
        score += r["points"]
        triggered.append("payment_failures")

    # Too many distinct devices in a short window (account sharing/takeover)
    r = cfg["many_devices"]
    if data["num_devices_30d"] > r["max_devices_30d"]:
        score += r["points"]
        triggered.append("many_devices")

    # Brand-new account already using huge amounts of data (subscription fraud)
    r = cfg["new_account_high_usage"]
    if data["account_age_days"] <= r["max_account_age_days"] and data["usage_mb"] >= r["min_usage_mb"]:
        score += r["points"]
        triggered.append("new_account_high_usage")

    normalized = min(score / cfg["max_raw_score"], 1.0)
    return normalized, triggered, hard_block
