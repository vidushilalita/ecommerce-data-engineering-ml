
import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from src.utils.storage import DataLakeStorage

def debug_ingestion():
    print("Debug: Starting ingestion test")
    
    # Read files
    try:
        users1 = pd.read_csv('data/users1.csv')
        print(f"Read users1: {len(users1)} rows")
        print("users1 dtypes:")
        print(users1.dtypes)
    except Exception as e:
        print(f"Failed to read users1: {e}")
        return

    try:
        users2 = pd.read_csv('data/users2.csv')
        print(f"Read users2: {len(users2)} rows")
        print("users2 dtypes:")
        print(users2.dtypes)
    except Exception as e:
        print(f"Failed to read users2: {e}")
        return
        
    # Check problematic values in users2
    print("\nChecking users2 age values:")
    print(users2['age'].unique()[:20])

    # Merge
    print("\nMerging...")
    merged = pd.concat([users1, users2], ignore_index=True)
    print(f"Merged: {len(merged)} rows")
    print("Merged dtypes:")
    print(merged.dtypes)
    
    # Try saving to parquet directly
    print("\nAttempting save to parquet...")
    try:
        merged.to_parquet('debug_users.parquet', index=False)
        print("✓ Save successful!")
    except Exception as e:
        print(f"✗ Save failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ingestion()
