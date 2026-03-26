import hashlib, pandas as pd
from pathlib import Path

df = pd.read_excel(r'd:\urja-ai\UrjaAI\recovered_files\other\metadata_1f5ea965567500ed7755255e403d8349bcfeb609.xlsx')
parquet_dir = Path(r'd:\urja-ai\UrjaAI\recovered_files\parquet_files')
parquet_stems = set(f.stem for f in parquet_dir.glob('*.parquet'))

print(f"Parquet files: {len(parquet_stems)}")
print(f"Metadata rows: {len(df)}")

# The parquet files are git blob hashes. Try hashing the file content path
file_col = df['file'].dropna().unique()
print(f"Unique metadata files: {len(file_col)}")

matches = 0
hash_map = {}  # hash -> original_path

for orig_path in file_col:
    # Try various hash inputs
    for candidate in [
        orig_path,
        orig_path.replace('/', '\\'),
        orig_path.split('/')[-1],  # just filename
        orig_path.split('/')[-1].replace('.parquet', ''),  # without ext
    ]:
        h = hashlib.sha1(candidate.encode('utf-8')).hexdigest()
        if h in parquet_stems:
            hash_map[h] = orig_path
            matches += 1
            if matches <= 3:
                print(f"  MATCH: sha1('{candidate}') = {h} -> {orig_path}")

print(f"\nTotal matches: {matches} / {len(file_col)}")

# If no match, try git blob hash format: "blob <size>\0<content>"
if matches == 0:
    print("\nTrying git blob format...")
    # Read first parquet, compute git blob hash, compare to filename
    first_parquet = sorted(parquet_dir.glob('*.parquet'))[0]
    content = first_parquet.read_bytes()
    git_header = f"blob {len(content)}\0".encode()
    git_hash = hashlib.sha1(git_header + content).hexdigest()
    print(f"  File: {first_parquet.name}")
    print(f"  Git blob hash of content: {git_hash}")
    print(f"  Filename stem: {first_parquet.stem}")
    print(f"  Match: {git_hash == first_parquet.stem}")
