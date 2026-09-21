"""
Trains a Random Forest model to predict the next hour's PM2.5 value from
the previous few hours' values (a "lag feature" approach - simple and a
good fit for a beginner ML project).

Run manually, separately from the Flask app:
    python ml/train_model.py "Delhi"

What it does, honestly:
  1. Downloads ~30 days of REAL hourly PM2.5 data for the given location
     from Open-Meteo (no API key, no synthetic data).
  2. Builds lag features: predict hour t from hours t-1, t-2, t-3.
  3. Splits into train/test BY TIME (not randomly - shuffling time series
     data leaks future information into training, which would fake the score).
  4. Trains a RandomForestRegressor.
  5. Prints MAE, RMSE, and R² on the held-out test set - whatever they are,
     good or bad. No cherry-picking.
  6. Saves an actual-vs-predicted plot to ml/evaluation_plot.png.
  7. Saves the trained model to ml/model.pkl for the Flask app to use.
"""

import sys
import os
import pickle

import numpy as np
import matplotlib
matplotlib.use("Agg")  # so this works without a display (e.g. over SSH)
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.geocode import geocode_location
from services.aqi_api import fetch_historical_pm25

LAG_COUNT = 3          # how many previous hours we use to predict the next one
PAST_DAYS = 30          # how much history to pull (Open-Meteo allows up to 92)
TEST_FRACTION = 0.2     # last 20% of the timeline held out for honest evaluation


def build_lag_dataset(values, lag_count):
    """
    Turns a plain list of numbers [v0, v1, v2, v3, ...] into:
      X = [[v0, v1, v2], [v1, v2, v3], ...]   (lag_count features per row)
      y = [v3, v4, ...]                        (the value right after each window)
    """
    X, y = [], []
    for i in range(len(values) - lag_count):
        X.append(values[i:i + lag_count])
        y.append(values[i + lag_count])
    return np.array(X), np.array(y)


def main():
    if len(sys.argv) < 2:
        print('Usage: python ml/train_model.py "City Name"')
        sys.exit(1)

    location_name = sys.argv[1]
    print(f"Looking up coordinates for '{location_name}'...")
    place = geocode_location(location_name)
    if place is None:
        print(f"Could not find '{location_name}'. Try a different spelling.")
        sys.exit(1)
    print(f"Found: {place['display_name']} ({place['latitude']}, {place['longitude']})")

    print(f"Downloading {PAST_DAYS} days of hourly PM2.5 history...")
    rows = fetch_historical_pm25(place["latitude"], place["longitude"], past_days=PAST_DAYS)

    # Drop any missing readings (the API sometimes has gaps).
    values = [v for _, v in rows if v is not None]
    print(f"Got {len(values)} valid hourly readings.")

    if len(values) < 50:
        print("Not enough data to train a meaningful model. Try a different location or increase PAST_DAYS.")
        sys.exit(1)

    X, y = build_lag_dataset(values, LAG_COUNT)

    # Time-based split: train on the earlier portion, test on the later portion.
    # This mimics real use (predicting the future from the past) and avoids
    # the classic time-series mistake of a random shuffle leaking future data into training.
    split_index = int(len(X) * (1 - TEST_FRACTION))
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples...")
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)

    print("\n--- Honest evaluation on held-out test data ---")
    print(f"MAE  (avg error, µg/m³): {mae:.2f}")
    print(f"RMSE (µg/m³):            {rmse:.2f}")
    print(f"R² (fit quality, 0-1):   {r2:.3f}")
    print("------------------------------------------------")
    print("These numbers are real - not tuned or cherry-picked. A low R² just")
    print("means PM2.5 here is noisy/hard to predict from 3 lag hours alone,")
    print("which is a legitimate and explainable finding, not a bug.\n")

    # Save an actual-vs-predicted plot so results can be inspected visually.
    plot_path = os.path.join(os.path.dirname(__file__), "evaluation_plot.png")
    plt.figure(figsize=(10, 5))
    plt.plot(y_test, label="Actual PM2.5", marker="o", markersize=3)
    plt.plot(predictions, label="Predicted PM2.5", marker="x", markersize=3)
    plt.title(f"Actual vs Predicted PM2.5 - {place['display_name']}")
    plt.xlabel("Test sample (chronological)")
    plt.ylabel("PM2.5 (µg/m³)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path)
    print(f"Saved evaluation plot to {plot_path}")

    # Save the trained model for the Flask app (services/predictor.py) to load.
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"Saved trained model to {model_path}")


if __name__ == "__main__":
    main()
