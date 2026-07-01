"""
Jarvis Data Analyst - Weather

Uses Open-Meteo (open-meteo.com) - free, no API key required, generous
rate limits for personal use. Low-risk / auto-execute tier.
"""

from dataclasses import dataclass

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes -> plain English
WEATHER_CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain",
    71: "light snow", 73: "moderate snow", 75: "heavy snow",
    80: "light rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    95: "thunderstorm", 96: "thunderstorm with light hail", 99: "thunderstorm with heavy hail",
}


@dataclass
class WeatherSummary:
    location: str
    temp_c: float
    feels_like_c: float
    condition: str
    humidity: int
    wind_kph: float
    precipitation_chance: int

    def spoken_summary(self, units: str = "metric") -> str:
        if units == "imperial":
            temp = self.temp_c * 9 / 5 + 32
            feels = self.feels_like_c * 9 / 5 + 32
            wind = self.wind_kph * 0.621371
            return (
                f"It's currently {temp:.0f}°F in {self.location}, feels like {feels:.0f}°F, "
                f"{self.condition}. Wind at {wind:.0f} mph, "
                f"{self.precipitation_chance} percent chance of precipitation."
            )
        return (
            f"It's currently {self.temp_c:.0f}°C in {self.location}, feels like "
            f"{self.feels_like_c:.0f}°C, {self.condition}. Wind at {self.wind_kph:.0f} kph, "
            f"{self.precipitation_chance} percent chance of precipitation."
        )


def _geocode(location: str) -> tuple[float, float, str]:
    resp = requests.get(GEOCODE_URL, params={"name": location, "count": 1}, timeout=10)
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        raise ValueError(f"Could not find location '{location}'")
    r = results[0]
    display_name = r.get("name", location)
    if r.get("admin1"):
        display_name += f", {r['admin1']}"
    return r["latitude"], r["longitude"], display_name


def get_weather_summary(location: str) -> WeatherSummary:
    lat, lon, display_name = _geocode(location)

    resp = requests.get(
        FORECAST_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                       "weather_code,wind_speed_10m,precipitation_probability",
        },
        timeout=10,
    )
    resp.raise_for_status()
    current = resp.json().get("current", {})

    code = current.get("weather_code", 0)
    condition = WEATHER_CODES.get(code, "unknown conditions")

    return WeatherSummary(
        location=display_name,
        temp_c=current.get("temperature_2m", 0.0),
        feels_like_c=current.get("apparent_temperature", 0.0),
        condition=condition,
        humidity=int(current.get("relative_humidity_2m", 0)),
        wind_kph=current.get("wind_speed_10m", 0.0),
        precipitation_chance=int(current.get("precipitation_probability", 0) or 0),
    )
