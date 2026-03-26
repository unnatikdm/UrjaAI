import duckdb
import pandas as pd

con = duckdb.connect(':memory:')

# Check a few rows of metadata
print(con.sql("SELECT file, object_id, device FROM 'metadata.parquet' LIMIT 10").df())
