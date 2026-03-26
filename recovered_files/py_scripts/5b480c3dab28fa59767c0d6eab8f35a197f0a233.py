import polars as pl

# This pattern looks for ANY parquet file anywhere inside the urjaai folder
root_path = r"C:\Users\elonm\urjaai\**\*.parquet"

# Use scan_parquet if you have gigabytes of data;
# it's "lazy," meaning it only loads what you need for your analysis.
df = pl.read_parquet(root_path)

print(f"Total rows loaded: {len(df)}")