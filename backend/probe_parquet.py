import pandas as pd
from pathlib import Path

d = Path(r'd:\urja-ai\UrjaAI\recovered_files\parquet_files')
files = sorted(d.glob('*.parquet'))
print(f'Total files: {len(files)}')

for f in [files[0], files[5000], files[15000], files[-1]]:
    df = pd.read_parquet(f)
    t = pd.to_datetime(df['time'], utc=True)
    print(f'{f.name}: rows={len(df)}, time={t.min()} - {t.max()}, data={df["data"].min():.2f}-{df["data"].max():.2f}')
