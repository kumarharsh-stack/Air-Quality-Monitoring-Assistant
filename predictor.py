"""
Loads the model trained by ml/train_model.py and uses it to predict the
next PM2.5 value for a location, based on the last few readings we have
stored in SQLite.

Returns None (instead of a fake number) if the model or enough history
doesn't exist yet - the "never fabricate results" rule applies here too.
"""

import os
import pickle
from services import db

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "model.pkl")

# Must match LAG_COUNT in ml/train_model.py - the model was trained on this many past values.
LAG_COUNT = 3


def predict_next_pm25(location: str):
    if not os.path.exists(MODEL_PATH):
        return None

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    history = db.get_history(location, limit=LAG_COUNT)
    if len(history) < LAG_COUNT:
        return None

    # Model expects features in the same order it was trained on: oldest -> newest lag values.
    lag_values = [row["pm2_5"] for row in history]
    if any(v is None for v in lag_values):
        return None

    prediction = model.predict([lag_values])[0]

    return {
        "location": location,
        "predicted_pm2_5": round(float(prediction), 2),
        "based_on_last_readings": lag_values,
        "note": "This is a simple lag-based Random Forest estimate, not a guarantee.",
    }
