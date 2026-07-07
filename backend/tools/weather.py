"""Tool: current weather via Open-Meteo (free, no API key required)."""

import requests
import structlog
from langchain_core.tools import tool

log = structlog.get_logger()

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather code → human-readable description
WMO_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


@tool
def get_weather(city: str) -> str:
    """
    Get the current weather for any city in the world.
    Returns temperature (Celsius), wind speed, and weather conditions.
    Uses the free Open-Meteo API — no API key needed.
    """
    log.info("weather_lookup", city=city)

    # Step 1: geocode the city name
    try:
        geo_params: dict[str, str | int] = {"name": city, "count": 1}
        geo = requests.get(GEOCODE_URL, params=geo_params, timeout=5).json()
    except Exception as exc:
        return f"Geocoding failed: {exc}"

    if not geo.get("results"):
        return f"Could not find location: '{city}'. Try a more specific city name."

    loc = geo["results"][0]
    lat, lon = float(loc["latitude"]), float(loc["longitude"])
    label = f"{loc['name']}, {loc.get('admin1', '')}, {loc.get('country', '')}".strip(", ")

    # Step 2: fetch current weather
    try:
        weather_params: dict[str, str | float] = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,weather_code",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
        }

        weather = requests.get(
            WEATHER_URL,
            params=weather_params,
            timeout=5,
        ).json()["current"]
    except Exception as exc:
        return f"Weather fetch failed: {exc}"

    condition = WMO_CODES.get(weather.get("weather_code", -1), "Unknown")

    return (
        f"Weather in {label}:\n"
        f"  Condition:   {condition}\n"
        f"  Temperature: {weather['temperature_2m']}°C\n"
        f"  Wind Speed:  {weather['wind_speed_10m']} km/h"
    )
