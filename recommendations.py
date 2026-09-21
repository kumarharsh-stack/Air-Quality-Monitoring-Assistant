"""
Turns a US AQI number into a plain-language health/activity recommendation.
Bands follow the official US EPA AQI breakpoints:
https://www.airnow.gov/aqi/aqi-basics/
"""

# Each entry: (max_aqi_for_this_band, level_name, color, advice)
BANDS = [
    (50, "Good", "#4ade80",
     "Air quality is satisfactory. It's a great day for outdoor activity."),
    (100, "Moderate", "#facc15",
     "Air quality is acceptable. Unusually sensitive people should consider "
     "reducing prolonged outdoor exertion."),
    (150, "Unhealthy for Sensitive Groups", "#fb923c",
     "Children, the elderly, and people with respiratory or heart conditions "
     "should limit prolonged outdoor exertion."),
    (200, "Unhealthy", "#f87171",
     "Everyone may begin to experience health effects. Limit prolonged "
     "outdoor exertion, especially sensitive groups."),
    (300, "Very Unhealthy", "#c084fc",
     "Health alert: everyone may experience more serious health effects. "
     "Avoid prolonged outdoor exertion."),
    (float("inf"), "Hazardous", "#7f1d1d",
     "Health warning of emergency conditions. Everyone should avoid all "
     "outdoor exertion and stay indoors if possible."),
]


def get_recommendation(us_aqi):
    """
    Returns {"level", "color", "advice"} for a given US AQI value.
    If us_aqi is missing (API didn't return one), we say so honestly
    instead of guessing a level.
    """
    if us_aqi is None:
        return {
            "level": "Unknown",
            "color": "#94a3b8",
            "advice": "AQI data wasn't available for this location right now.",
        }

    for max_aqi, level, color, advice in BANDS:
        if us_aqi <= max_aqi:
            return {"level": level, "color": color, "advice": advice}

    # Should never reach here because the last band's max is infinity.
    return {"level": "Unknown", "color": "#94a3b8", "advice": "Unable to classify this AQI value."}
