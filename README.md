# Air Quality Assistant

A beginner-friendly, end-to-end air quality web app: live AQI lookup by city,
health recommendations, historical chart, a Random Forest ML prediction,
and a rule-based assistant (with an optional Claude-powered upgrade).

Built as a learning/portfolio project — no API key required to run it.

## Stack
- **Backend:** Flask
- **Data source:** Open-Meteo Geocoding + Air Quality APIs (free, no key)
- **Storage:** SQLite (`data/air_quality.db`, created automatically)
- **ML:** scikit-learn RandomForestRegressor
- **Frontend:** plain HTML/CSS/JS + Chart.js (via CDN)

## Project structure
```
air-quality-assistant/
├── app.py                    # Flask app and all routes
├── requirements.txt
├── services/
│   ├── geocode.py             # city name -> lat/lon
│   ├── aqi_api.py              # current + historical AQI from Open-Meteo
│   ├── db.py                   # SQLite read/write
│   ├── recommendations.py      # AQI -> health advice
│   ├── assistant.py            # rule-based Q&A (+ optional Claude API)
│   └── predictor.py            # loads ml/model.pkl for predictions
├── ml/
│   └── train_model.py          # standalone script: trains and evaluates the model
├── templates/index.html
├── static/css/style.css
├── static/js/main.js
└── data/                       # SQLite database lives here (created at runtime)
```

## 1. Setup

```bash
cd air-quality-assistant
python -m venv venv
```

Activate it:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

Install dependencies:
```bash
pip install -r requirements.txt
```

## 2. Run the web app

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser. Search any city — e.g. "Delhi",
"London", "New York". Each search:
- geocodes the city,
- pulls the current AQI/pollutants,
- saves it to SQLite,
- shows the health recommendation, history chart, and enables the assistant.

## 3. (Optional) Train the ML model

The prediction feature needs a trained model first. This is a **separate,
one-time step** — not part of the web app's normal flow, because training
takes a few seconds and downloads real historical data.

```bash
python ml/train_model.py "Delhi"
```

This will:
1. Download ~30 days of real hourly PM2.5 history for that city.
2. Train a Random Forest to predict the next hour's PM2.5 from the previous 3 hours.
3. Print **honest** MAE / RMSE / R² on held-out test data (no cherry-picking).
4. Save a plot to `ml/evaluation_plot.png`.
5. Save the model to `ml/model.pkl`.

Once trained, go back to the running web app, search that same city a few
times (so there's enough recent history in SQLite — at least 3 readings),
and click **"Predict next PM2.5"**.

> Note: the model is per-app, not per-city — if you train it on Delhi's data,
> it's only meaningful for predicting Delhi (or similarly-polluted cities).
> That's a real limitation worth mentioning in an interview, not something to hide.

## 4. (Optional) Enable the LLM-powered assistant

By default, the assistant answers using simple keyword rules — no API key,
no cost, always available. To upgrade it to use Claude for more natural
answers:

```bash
pip install anthropic
```

Then set an environment variable before running the app:
- Windows (PowerShell): `$env:ANTHROPIC_API_KEY="your-key-here"`
- macOS/Linux: `export ANTHROPIC_API_KEY="your-key-here"`

If the key isn't set, or the API call fails for any reason, the app
automatically falls back to the rule-based answer — it never crashes because
of this feature.

## Known limitations (worth saying out loud in an interview)
- The ML model uses only 3 lag hours as features — a real production system
  would add weather, time-of-day, and location features.
- History is only what you've personally searched since running the app —
  it's not a continuously-running background collector (a good "future work" item).
- The AQI prediction model is city-specific once trained; it isn't a general model.
