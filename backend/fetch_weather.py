"""
fetch_weather.py — Download real Mumbai weather from Open-Meteo.

Run from backend/:
    python fetch_weather.py

Saves: backend/mumbai_weather_2025.csv
Columns: date, temperature, humidity, apparent_temp, precipitation
"""
import json
import urllib.request
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent / "mumbai_weather_2025.csv"

# Mumbai coordinates
LAT, LON = 19.076, 72.878

# Open-Meteo historical weather archive API (free, no key needed)
URL = (
    f"https://archive-api.open-meteo.com/v1/archive?"
    f"latitude={LAT}&longitude={LON}"
    f"&start_date=2025-01-01&end_date=2025-07-31"
    f"&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation"
    f"&timezone=UTC"
)


def fetch():
    print("Fetching real Mumbai weather from Open-Meteo...")
    print(f"  URL: {URL[:80]}...")

    req = urllib.request.Request(URL)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    hourly = data["hourly"]
    df = pd.DataFrame({
        "date": pd.to_datetime(hourly["time"], utc=True),
        "temperature": hourly["temperature_2m"],
        "humidity": hourly["relative_humidity_2m"],
        "apparent_temp": hourly["apparent_temperature"],
        "precipitation": hourly["precipitation"],
    })

    df.to_csv(OUT, index=False)
    print(f"✅ Saved {len(df)} hourly rows → {OUT}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Temp range: {df['temperature'].min():.1f}°C to {df['temperature'].max():.1f}°C")


if __name__ == "__main__":
    fetch()
