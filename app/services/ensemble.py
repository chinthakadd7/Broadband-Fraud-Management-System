"""
Combines the rule-based score and ML score into one final decision.

Strategy: weighted average, with a "hard block" override for rules
that should never be second-guessed by the ML model (e.g. a device
that's on a known fraud blacklist).
"""

from typing import Dict

RULE_WEIGHT = 0.4
ML_WEIGHT = 0.6

BLOCK_THRESHOLD = 0.7
REVIEW_THRESHOLD = 0.4


def ensemble_predict(rule_score: float, ml_score: float, hard_block: bool) -> Dict:
    if hard_block:
        return {"final_score": 1.0, "decision": "BLOCK"}

    final_score = (RULE_WEIGHT * rule_score) + (ML_WEIGHT * ml_score)

    if final_score >= BLOCK_THRESHOLD:
        decision = "BLOCK"
    elif final_score >= REVIEW_THRESHOLD:
        decision = "REVIEW"
    else:
        decision = "ALLOW"

    return {"final_score": round(final_score, 4), "decision": decision}
