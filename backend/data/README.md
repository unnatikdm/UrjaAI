# Place per-building CSV files here named {building_id}.csv
# e.g. main_library.csv, engineering_block.csv, etc.
#
# Required columns:
#   timestamp        (ISO 8601, e.g. 2025-12-01T08:00:00Z)
#   building_id      (string matching the filename prefix)
#   consumption_kwh  (float)
#   temperature_c    (float)
#   occupancy        (float 0.0–1.0)
#   humidity_pct     (float)
#
# If no CSV is present the backend auto-generates synthetic data as a fallback.
