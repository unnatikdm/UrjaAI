# UrjaAI Data Analysis with DuckDB

All data from the `urjaai` directory has been loaded into a DuckDB database named `urjaai.db`.

## Database Schema

### `metadata` Table
Contains metadata for sensors and devices.
- **Key Columns**: `object_id`, `device`, `file`, `building`, `floor`, etc.
- **Reference**: Join with `sensors` using the `file` column.

### `sensors` Table
Contains raw sensor readings from 37,000+ parquet files.
- **Columns**: `time`, `data`, `source_file`, `__index_level_0__`.
- **Note**: `source_file` is the full path to the parquet file.

## Example Queries

### Joining Metadata with Sensor Data
To get sensor readings for a specific device:
```sql
SELECT m.device, s.time, s.data
FROM sensors s
JOIN metadata m ON s.source_file LIKE '%' || m.file
LIMIT 10;
```

### Counting Rows
```sql
SELECT count(*) FROM sensors;
```

### Finding Active Devices
```sql
SELECT device, count(*) as readings
FROM metadata m
JOIN sensors s ON s.source_file LIKE '%' || m.file
GROUP BY device
ORDER BY readings DESC
LIMIT 10;
```

## How to use in Python
```python
import duckdb
con = duckdb.connect('urjaai.db')
df = con.execute("SELECT * FROM sensors LIMIT 10").df()
print(df)
```
