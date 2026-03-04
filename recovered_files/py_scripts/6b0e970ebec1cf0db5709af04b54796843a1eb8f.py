import duckdb
con = duckdb.connect('urjaai.db')
print("--- Database Stats ---")
print("Tables:", con.execute("SHOW TABLES").fetchall())
print("\nMetadata count:", con.execute("SELECT count(*) FROM metadata").fetchone()[0])
print("Sensors count:", con.execute("SELECT count(*) FROM sensors").fetchone()[0])
print("Unique files in sensors:", con.execute("SELECT count(distinct source_file) FROM sensors").fetchone()[0])

print("\nSample Metadata (first 5):")
print(con.execute("SELECT object_id, device, file FROM metadata LIMIT 5").df())

print("\nSample Sensors (first 5):")
print(con.execute("SELECT * FROM sensors LIMIT 5").df())
con.close()
