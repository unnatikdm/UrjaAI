import duckdb
import os
import glob
import time

db_path = 'urjaai.db'
if os.path.exists(db_path):
    print(f"Removing existing {db_path}...")
    os.remove(db_path)

con = duckdb.connect(db_path)

# 1. Load Metadata
print("Loading metadata.parquet into table 'metadata'...")
con.execute("CREATE TABLE metadata AS SELECT * FROM read_parquet('metadata.parquet')")
print("Metadata loaded.")

# 2. Load Sensors
print("Loading sensor data from all RBHU-2025-* directories...")
print("This may take a few minutes as there are ~37,000 files...")

start_time = time.time()

# Using a glob to load all parquets in subdirectories
# filename=True adds a column 'filename' with the source file path
# union_by_name=True handles cases where schemas might differ slightly
con.execute("""
    CREATE TABLE sensors AS 
    SELECT *, filename as source_file
    FROM read_parquet('RBHU-2025-*/**/*.parquet', union_by_name=True, filename=True)
""")

end_time = time.time()
duration = end_time - start_time

print(f"Sensor data loaded in {duration:.2f} seconds.")

# 3. Quick Stats
print("\n--- Summary ---")
con.sql("SELECT count(*) as total_metadata_rows FROM metadata").show()
con.sql("SELECT count(*) as total_sensor_rows FROM sensors").show()
con.sql("SELECT count(distinct source_file) as unique_files_loaded FROM sensors").show()

print("\nDatabase 'urjaai.db' is ready for analysis!")
con.close()
