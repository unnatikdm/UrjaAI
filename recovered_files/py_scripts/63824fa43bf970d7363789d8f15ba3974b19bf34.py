import duckdb
import glob
import os

con = duckdb.connect(':memory:')

print("--- metadata.parquet Sample ---")
try:
    con.sql("SELECT * FROM read_parquet('metadata.parquet') LIMIT 5").show()
except Exception as e:
    print(e)

print("\n--- Sensor parquet Sample (first file found) ---")
parquet_files = glob.glob('RBHU-2025-*/**/*.parquet', recursive=True)
if parquet_files:
    first_sensor = parquet_files[0]
    print(f"File: {first_sensor}")
    try:
        con.sql(f"SELECT * FROM read_parquet('{first_sensor}') LIMIT 5").show()
    except Exception as e:
        print(e)
else:
    print("No sensor parquet files found in subdirectories.")


print("\n--- First 5 Parquet Files ---")
for f in parquet_files[:5]:
    print(f)


