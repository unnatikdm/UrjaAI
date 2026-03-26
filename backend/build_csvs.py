"""
build_csvs.py — Split raw parquet sensor files into per-building CSVs.

Run from backend/:
    python build_csvs.py

Creates 7 CSV files in backend/data/, one per building.
Each CSV has columns: timestamp, building_id, consumption_kwh, temperature_c, occupancy, humidity_pct
"""
import math
import random
from pathlib import Path
from datetime import datetime

import pandas as pd

PARQUET_DIR = Path(__file__).parent.parent / "recovered_files" / "parquet_files"
DATA_DIR    = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

BUILDINGS = [
    "main_library",
    "engineering_block",
    "admin_block",
    "sports_complex",
    "hostel_a",
    "hostel_b",
    "cafeteria",
]


def build_csvs():
    files = sorted(PARQUET_DIR.glob("*.parquet"))
    n = len(files)
    print(f"Found {n} parquet files in {PARQUET_DIR}")

    if n == 0:
        print("ERROR: No parquet files found!")
        return

    # Split files evenly across buildings
    chunk = n // len(BUILDINGS)

    for i, bld in enumerate(BUILDINGS):
        start = i * chunk
        end   = start + chunk if i < len(BUILDINGS) - 1 else n
        bld_files = files[start:end]

        print(f"\n[{bld}] Loading {len(bld_files)} sensor files...")

        frames = []
        for f in bld_files:
            try:
                df = pd.read_parquet(f)
                frames.append(df)
            except Exception:
                continue

        if not frames:
            print(f"  WARNING: No valid data for {bld}, skipping.")
            continue

        combined = pd.concat(frames, ignore_index=True)
        combined["time"] = pd.to_datetime(combined["time"], utc=True)
        combined = combined.sort_values("time")

        # Resample to hourly mean (raw data is in Watts)
        hourly = combined.set_index("time")["data"].resample("h").mean().dropna()

        # Convert W → kWh (1 hour at average W)
        hourly = hourly / 1000.0

        rng = random.Random(sum(ord(c) for c in bld))

        rows = []
        for ts, kwh in hourly.items():
            # Derive realistic occupancy from hour of day
            hour = ts.hour
            if 8 <= hour <= 18:
                occ = 0.6 + 0.3 * math.sin(math.pi * (hour - 8) / 10)
            elif 6 <= hour <= 22:
                occ = 0.2 + 0.1 * math.sin(math.pi * (hour - 6) / 16)
            else:
                occ = 0.05

            # Derive temperature from month/hour (Mumbai-like)
            month = ts.month
            base_temp = 28 + 4 * math.sin(math.pi * (month - 3) / 6)
            temp = base_temp + 5 * math.sin(math.pi * hour / 12) + rng.uniform(-1.5, 1.5)

            # Humidity (higher in monsoon Jun-Sep)
            humid = 60 + (20 if 6 <= month <= 9 else 0) + rng.uniform(-8, 8)

            rows.append({
                "timestamp": ts.isoformat(),
                "building_id": bld,
                "consumption_kwh": round(float(kwh), 4),
                "temperature_c": round(temp, 1),
                "occupancy": round(occ, 2),
                "humidity_pct": round(min(100, humid), 1),
            })

        out = DATA_DIR / f"{bld}.csv"
        pd.DataFrame(rows).to_csv(out, index=False)
        print(f"  Saved {len(rows)} hourly rows → {out}")

    print("\n✅ All building CSVs created in", DATA_DIR)


if __name__ == "__main__":
    build_csvs()
