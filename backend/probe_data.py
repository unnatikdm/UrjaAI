"""Probe parquet files to understand structure for real data pipeline."""
import pandas as pd
from pathlib import Path
import random

d = Path(r'd:\urja-ai\UrjaAI\recovered_files\parquet_files')
files = sorted(d.glob('*.parquet'))
print(f"Total parquet files: {len(files)}")

# Sample 10 spread across the range
sample_idx = [0, len(files)//10, len(files)//5, len(files)//3, len(files)//2,
              2*len(files)//3, 3*len(files)//4, 4*len(files)//5, 9*len(files)//10, -1]
for i in sample_idx:
    f = files[i]
    df = pd.read_parquet(f)
    t = pd.to_datetime(df['time'], utc=True)
    print(f"  {f.name}: rows={len(df):>5}, "
          f"time={t.min().strftime('%Y-%m-%d')} to {t.max().strftime('%Y-%m-%d')}, "
          f"data={df['data'].min():.1f} - {df['data'].max():.1f}")

# Check total unique timestamps across a sample
print("\n--- Aggregated stats from 50 random files ---")
random.seed(42)
sample = random.sample(files, min(50, len(files)))
frames = [pd.read_parquet(f) for f in sample]
combined = pd.concat(frames, ignore_index=True)
combined['time'] = pd.to_datetime(combined['time'], utc=True)
print(f"  Combined rows: {len(combined)}")
print(f"  Date range: {combined['time'].min()} to {combined['time'].max()}")
print(f"  Data range: {combined['data'].min():.2f} to {combined['data'].max():.2f}")
print(f"  Data mean: {combined['data'].mean():.2f}")
print(f"  Unique dates: {combined['time'].dt.date.nunique()}")

# Row counts distribution
row_counts = [len(pd.read_parquet(f)) for f in random.sample(files, min(100, len(files)))]
print(f"\n--- Row count distribution (100 files) ---")
print(f"  min={min(row_counts)}, max={max(row_counts)}, mean={sum(row_counts)/len(row_counts):.0f}")
