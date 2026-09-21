"""
Turns a location name (e.g. "Delhi") into latitude/longitude using
Open-Meteo's free Geocoding API. No API key needed.
Docs: https://open-meteo.com/en/docs/geocoding-api
"""

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def geocode_location(name: str):
    """
    Returns a dict: {"display_name", "latitude", "longitude"}
    or None if nothing matched.
    """
    response = requests.get(
        GEOCODING_URL,
        params={"name": name, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()  # raises an exception on a bad HTTP status
    data = response.json()

    results = data.get("results")
    if not results:
        return None

    place = results[0]

    # Build a readable name like "Delhi, India" from whatever fields exist.
    parts = [place.get("name")]
    if place.get("admin1"):
        parts.append(place["admin1"])
    if place.get("country"):
        parts.append(place["country"])
    display_name = ", ".join(p for p in parts if p)

    return {
        "display_name": display_name,
        "latitude": place["latitude"],
        "longitude": place["longitude"],
    }
