"""
The "AI assistant" feature.

Default behaviour: simple rule-based keyword matching, using the location's
latest stored reading for context. This works with ZERO setup and zero cost.

Optional upgrade: if an ANTHROPIC_API_KEY environment variable is set, we
also send the question to Claude for a more natural-language answer, with
the latest reading given as context so it doesn't hallucinate numbers.

If the key isn't set (the default), the app never calls out to any LLM
and works fully offline apart from the air quality API itself.
"""

import os
from services.recommendations import get_recommendation

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def _rule_based_answer(question: str, latest: dict) -> str:
    q = question.lower()

    if latest is None:
        context_line = "I don't have a recent reading for this location yet - try searching it first."
    else:
        rec = get_recommendation(latest["us_aqi"])
        context_line = (
            f"The latest reading for {latest['location']} was AQI {latest['us_aqi']} "
            f"({rec['level']}), PM2.5 {latest['pm2_5']} µg/m³."
        )

    if any(word in q for word in ["run", "jog", "exercise", "outdoor", "walk", "gym"]):
        if latest and latest["us_aqi"] is not None and latest["us_aqi"] > 100:
            return f"{context_line} I'd suggest keeping exercise indoors today, or shortening outdoor sessions."
        return f"{context_line} Outdoor exercise looks fine right now."

    if any(word in q for word in ["mask", "n95"]):
        if latest and latest["us_aqi"] is not None and latest["us_aqi"] > 150:
            return f"{context_line} A well-fitted N95 mask is a reasonable precaution outdoors today."
        return f"{context_line} A mask isn't really necessary at this level, but sensitive individuals can still choose to wear one."

    if any(word in q for word in ["window", "ventilat", "air out"]):
        if latest and latest["us_aqi"] is not None and latest["us_aqi"] > 150:
            return f"{context_line} I'd keep windows closed and use an air purifier indoors if you have one."
        return f"{context_line} It's a fine time to open windows for ventilation."

    if any(word in q for word in ["mean", "what is aqi", "explain", "scale"]):
        return (
            "AQI (Air Quality Index) is a 0-500 scale: 0-50 Good, 51-100 Moderate, "
            "101-150 Unhealthy for Sensitive Groups, 151-200 Unhealthy, "
            "201-300 Very Unhealthy, 301+ Hazardous. " + context_line
        )

    # Default fallback for anything we don't have a specific rule for.
    return context_line + " Ask me about exercise, masks, ventilation, or what the AQI scale means."


def _llm_answer(question: str, latest: dict) -> str:
    """
    Calls the Anthropic API for a more natural answer. Only used if
    ANTHROPIC_API_KEY is set. Any failure here falls back to the rule-based
    answer rather than crashing the request.
    """
    try:
        import anthropic  # imported lazily so the package is only required if you use this feature
    except ImportError:
        return _rule_based_answer(question, latest)

    context = "No recent air quality reading is available." if latest is None else (
        f"Location: {latest['location']}, US AQI: {latest['us_aqi']}, "
        f"PM2.5: {latest['pm2_5']} µg/m3, PM10: {latest['pm10']} µg/m3."
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    "You are an air quality assistant. Use only the data given below - "
                    "never invent AQI numbers. Answer briefly and practically.\n\n"
                    f"Data: {context}\n\nQuestion: {question}"
                ),
            }],
        )
        return response.content[0].text
    except Exception:
        # If the API call fails for any reason (bad key, network, rate limit),
        # silently fall back rather than showing the user a raw exception.
        return _rule_based_answer(question, latest)


def answer_question(question: str, latest: dict) -> str:
    if ANTHROPIC_API_KEY:
        return _llm_answer(question, latest)
    return _rule_based_answer(question, latest)
