"""
Persists generated signals to a local JSON file so they can be graded
later, once enough calendar time has passed for 5-day/20-day forward
returns to actually exist. You cannot backtest a signal generated five
minutes ago -- there's no future price yet.
"""

import json
import os
from datetime import datetime

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "demo_data", "signal_log.json")


def _serialize(record: dict) -> dict:
    out = dict(record)
    out["date"] = record["date"].isoformat() if isinstance(record["date"], datetime) else record["date"]
    for key in ["multi_agent_direction", "sentiment_baseline_direction", "random_baseline_direction"]:
        val = out.get(key)
        out[key] = val.value if hasattr(val, "value") else val
    return out


def save_signal(record: dict) -> None:
    existing = load_signals()
    existing.append(_serialize(record))
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w") as f:
        json.dump(existing, f, indent=2)


def load_signals() -> list[dict]:
    if not os.path.exists(STORE_PATH):
        return []
    with open(STORE_PATH, "r") as f:
        return json.load(f)
