#!/usr/bin/env python3
"""
Migration script to convert existing JSON array files to NDJSON format.
Run this once to convert historical data.
"""
import json
import os
import sys
from glob import glob

def migrate_json_to_ndjson(json_file):
    """Convert a JSON array file to NDJSON format."""
    ndjson_file = json_file.replace('.json', '.ndjson')
    
    # Skip if already migrated
    if os.path.exists(ndjson_file):
        print(f"Skipping {json_file} - NDJSON file already exists")
        return False
    
    try:
        # Read the JSON array
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Write as NDJSON
        with open(ndjson_file, 'w') as f:
            for entry in data:
                json.dump(entry, f, separators=(',', ':'))
                f.write('\n')
        
        print(f"Migrated {json_file} -> {ndjson_file} ({len(data)} entries)")
        
        # Optionally rename old file
        os.rename(json_file, json_file + '.backup')
        print(f"Renamed original to {json_file}.backup")
        
        return True
    except Exception as e:
        print(f"Error migrating {json_file}: {e}")
        return False

def main():
    data_dir = os.environ.get('DATA_DIR', '/data/smartsolar-v1')
    
    # Find all JSON files
    json_files = glob(os.path.join(data_dir, 'data_*.json'))
    
    if not json_files:
        print(f"No JSON files found in {data_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files to migrate")
    
    migrated = 0
    for json_file in json_files:
        if migrate_json_to_ndjson(json_file):
            migrated += 1
    
    print(f"\nMigration complete: {migrated}/{len(json_files)} files migrated")

if __name__ == "__main__":
    main() 