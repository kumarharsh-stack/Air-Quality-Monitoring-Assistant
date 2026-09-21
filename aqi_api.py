"""
Fetches current air quality data from Open-Meteo's Air Quality API.
No API key needed.
Docs: https://open-meteo.com/en/docs/air-quality-api
"""

import requests

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# The "current" fields we ask Open-Meteo for on every request.
CURRENT_FIELDS = "us_aqi,pm2_5,pm10,ozone,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide"


def fetch_current_air_quality(latitude: float, longitude: float) -> dict:
    """
    Returns a dict with the current pollutant readings and the US AQI value
    (0-500 scale, the one most people recognize from the news).
    Raises an exception if the request fails - we let app.py decide how
    to present that to the user, instead of swallowing it here.
    """
    response = requests.get(
        AIR_QUALITY_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": CURRENT_FIELDS,
            "timezone": "auto",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    current = data["current"]
    return {
        "time": current.get("time"),
        "us_aqi": current.get("us_aqi"),
        "pm2_5": current.get("pm2_5"),
        "pm10": current.get("pm10"),
        "ozone": current.get("ozone"),
        "nitrogen_dioxide": current.get("nitrogen_dioxide"),
        "sulphur_dioxide": current.get("sulphur_dioxide"),
        "carbon_monoxide": current.get("carbon_monoxide"),
    }


def fetch_historical_pm25(latitude: float, longitude: float, past_days: int = 30):
    """
    Used only by ml/train_model.py. Returns a list of (time, pm2_5) tuples
    for the last `past_days` days of hourly data (Open-Meteo allows up to 92).
    """
    response = requests.get(
        AIR_QUALITY_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "pm2_5",
            "past_days": past_days,
            "timezone": "auto",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    times = data["hourly"]["time"]
    values = data["hourly"]["pm2_5"]
    return list(zip(times, values))
