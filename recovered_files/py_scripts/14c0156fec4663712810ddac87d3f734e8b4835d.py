import duckdb
import glob

con = duckdb.connect(':memory:')

def get_columns(path):
    try:
        return con.sql(f"SELECT * FROM '{path}' LIMIT 0").columns
    except Exception as e:
        return str(e)

with open('columns_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"metadata.parquet columns: {get_columns('metadata.parquet')}\n\n")
    
    parquet_files = glob.glob('RBHU-2025-*/**/*.parquet', recursive=True)
    if parquet_files:
        f.write(f"Total sensor files: {len(parquet_files)}\n")
        f.write(f"First sensor file ({parquet_files[0]}) columns: {get_columns(parquet_files[0])}\n")
        if len(parquet_files) > 1:
            f.write(f"Second sensor file ({parquet_files[1]}) columns: {get_columns(parquet_files[1])}\n")
    else:
        f.write("No sensor files found.\n")
