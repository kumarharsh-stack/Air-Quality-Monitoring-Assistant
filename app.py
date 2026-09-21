

from flask import Flask, render_template, request, jsonify
import os

from services.geocode import geocode_location
from services.aqi_api import fetch_current_air_quality
from services import db
from services.recommendations import get_recommendation
from services.assistant import answer_question
from services.predictor import predict_next_pm25

app = Flask(__name__)

# Create the SQLite table (if it doesn't already exist) as soon as the app starts.
db.init_db()


@app.route("/")
def home():
    """Serve the single-page frontend."""
    return render_template("index.html", app_name="Air Quality Assistant")


@app.route("/api/search", methods=["POST"])
def search():
    """
    Body: { "location": "Delhi" }

    Steps:
      1. Turn the city name into coordinates (geocoding).
      2. Ask Open-Meteo for the current air quality at those coordinates.
      3. Save the reading to SQLite so it becomes part of the location's history.
      4. Attach a plain-language health recommendation.
      5. Return everything the frontend needs to render.
    """
    data = request.get_json(silent=True) or {}
    location_name = (data.get("location") or "").strip()

    if not location_name:
        return jsonify({"error": "Please enter a location."}), 400

    place = geocode_location(location_name)
    if place is None:
        return jsonify({"error": f"Could not find a place called '{location_name}'."}), 404

    try:
        reading = fetch_current_air_quality(place["latitude"], place["longitude"])
    except Exception as exc:
        # We never hide the real error behind a vague message - that makes debugging painful.
        return jsonify({"error": f"Failed to fetch air quality data: {exc}"}), 502

    # Persist this reading so /api/history and the ML model have data to use later.
    db.insert_reading(
        location=place["display_name"],
        latitude=place["latitude"],
        longitude=place["longitude"],
        us_aqi=reading["us_aqi"],
        pm2_5=reading["pm2_5"],
        pm10=reading["pm10"],
        ozone=reading["ozone"],
        no2=reading["nitrogen_dioxide"],
    )

    recommendation = get_recommendation(reading["us_aqi"])

    return jsonify({
        "location": place["display_name"],
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "reading": reading,
        "recommendation": recommendation,
    })


@app.route("/api/history")
def history():
    """
    Query param: ?location=Delhi
    Returns the readings we have stored for that location, oldest first,
    for the frontend to plot on a Chart.js line chart.
    """
    location_name = request.args.get("location", "").strip()
    if not location_name:
        return jsonify({"error": "Missing location parameter."}), 400

    rows = db.get_history(location_name, limit=50)
    return jsonify({"location": location_name, "history": rows})


@app.route("/api/predict")
def predict():
    """
    Query param: ?location=Delhi
    Uses the trained ML model (see ml/train_model.py) to predict the next
    PM2.5 value from the most recent stored readings for that location.
    If the model hasn't been trained yet, this says so honestly instead
    of faking a number.
    """
    location_name = request.args.get("location", "").strip()
    if not location_name:
        return jsonify({"error": "Missing location parameter."}), 400

    result = predict_next_pm25(location_name)
    if result is None:
        return jsonify({
            "error": "No trained model found, or not enough history for this "
                     "location yet. Run ml/train_model.py first, and search "
                     "this location a few times to build up history."
        }), 404

    return jsonify(result)


@app.route("/api/assistant", methods=["POST"])
def assistant():
    """
    Body: { "location": "Delhi", "question": "Should I go for a run?" }
    Rule-based by default. If ANTHROPIC_API_KEY is set in the environment,
    the question is additionally passed to Claude for a more natural answer.
    The app works fully without any key.
    """
    data = request.get_json(silent=True) or {}
    location_name = (data.get("location") or "").strip()
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Please ask a question."}), 400

    latest = db.get_latest_reading(location_name) if location_name else None
    answer = answer_question(question, latest)
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(debug=True)
