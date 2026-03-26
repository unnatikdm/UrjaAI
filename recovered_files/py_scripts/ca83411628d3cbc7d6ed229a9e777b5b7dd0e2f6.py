import duckdb
import os

db_path = 'urjaai.db'
if os.path.exists(db_path):
    os.remove(db_path)

con = duckdb.connect(db_path)

print("Loading metadata...")
con.execute("CREATE TABLE metadata AS SELECT * FROM read_parquet('metadata.parquet')")

print("Loading sensor data (testing with first directory)...")
# Test with one directory first to see if it works
try:
    con.execute("""
        CREATE TABLE sensors AS 
        SELECT *, regexp_extract(filename, 'RBHU-2025-\\d{2}\\\\ (.*)', 1) as relative_path
        FROM read_parquet('RBHU-2025-01/**/*.parquet', union_by_name=True, filename=True)
    """)
    print("Test load successful.")
    con.execute("SELECT count(*) FROM sensors").show()
except Exception as e:
    print(f"Error during test load: {e}")
