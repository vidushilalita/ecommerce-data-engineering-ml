# Task 2-3: Data Collection, Ingestion & Raw Data Storage

## Overview

This document describes the data ingestion pipeline and raw data storage implementation for the RecoMart recommendation system.

---

## 1. Data Sources

| Source | Format | Records | Update Frequency | File Location |
|--------|--------|---------|------------------|---------------|
| User Profiles | CSV | 927 users | Daily batch | `data/users1.csv`, `data/users2.csv` |
| Product Catalog | JSON | 101 products | On-demand | `data/products.json` |
| User Transactions | CSV | 3,001 records | Near real-time | `data/transactions.csv` |

---

## 2. Ingestion Scripts

### 2.1 User Data Ingestion
**File**: `src/ingestion/ingest_users.py`

```python
class UserDataIngestion:
    """Handles ingestion of user data from CSV sources"""
```

**Features**:
- Reads multiple CSV files (`users1.csv`, `users2.csv`)
- Merges datasets and handles duplicates
- Validates user_id, age (18-65), gender (M/F), device
- Cleans string columns and removes NaN values
- Stores in partitioned Parquet format
- Archives processed source files with timestamps

**Execution**:
```bash
python -m src.ingestion.ingest_users
```

### 2.2 Product Data Ingestion
**File**: `src/ingestion/ingest_products.py`

```python
class ProductDataIngestion:
    """Handles ingestion of product data from JSON source"""
```

**Features**:
- Reads JSON file with nested product structures
- Flattens JSON to tabular DataFrame
- Validates item_id, price (>0), rating (1-5), category, brand
- Checks for duplicate item_ids
- Stores in partitioned Parquet format

**Execution**:
```bash
python -m src.ingestion.ingest_products
```

### 2.3 Transaction Data Ingestion
**File**: `src/ingestion/ingest_transactions.py`

```python
class TransactionDataIngestion:
    """Handles ingestion of transaction/interaction data from CSV source"""
```

**Features**:
- Reads transaction CSV with user-item interactions
- Parses timestamps to datetime format
- Validates view_mode values (view, add_to_cart, purchase)
- Validates rating range (1-5)
- Validates foreign keys (user_id, item_id)
- Archives processed files with timestamps

**Execution**:
```bash
python -m src.ingestion.ingest_transactions
```

---

## 3. Error Handling and Retry Mechanisms

### 3.1 Exception Handling
All ingestion scripts implement comprehensive error handling:

```python
try:
    df = pd.read_csv(file_path)
    logger.info(f"Read {len(df)} records from {filename}")
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    raise
except pd.errors.EmptyDataError:
    logger.error(f"File is empty: {file_path}")
    raise
except Exception as e:
    logger.error(f"Error reading {filename}: {str(e)}")
    raise
```

### 3.2 Prefect Flow with Retries
The Prefect orchestration includes retry logic:

```python
@task(name="Ingest Users", retries=2, retry_delay_seconds=60)
def ingest_users(target_date: str = None):
    """Run user data ingestion with automatic retries"""
    from src.ingestion.ingest_users import UserDataIngestion
    ingestion = UserDataIngestion(ingestion_date=target_date)
    result = ingestion.ingest()
    return result
```

---

## 4. Logging System

### 4.1 Logger Configuration
**File**: `src/utils/logger.py`

Features:
- Colored console output for different log levels
- Rotating file logs (10MB max, 5 backups)
- Structured format with timestamps and module names

```python
from src.utils.logger import get_logger
logger = get_logger(__name__)

logger.info("Starting ingestion...")
logger.warning("Found duplicate records")
logger.error("Ingestion failed")
```

### 4.2 Log Output Location
- Console: Real-time colored output
- Files: `logs/{module_name}.log`

### 4.3 Sample Log Output
```
2026-01-22 18:30:00 - src.ingestion.ingest_users - INFO - ============================================================
2026-01-22 18:30:00 - src.ingestion.ingest_users - INFO - Starting User Data Ingestion
2026-01-22 18:30:00 - src.ingestion.ingest_users - INFO - ============================================================
2026-01-22 18:30:01 - src.ingestion.ingest_users - INFO - Step 1: Validating source files...
2026-01-22 18:30:01 - src.ingestion.ingest_users - INFO -  Found users1.csv
2026-01-22 18:30:01 - src.ingestion.ingest_users - INFO -  Found users2.csv
2026-01-22 18:30:02 - src.ingestion.ingest_users - INFO - Read 500 records from users1.csv
2026-01-22 18:30:02 - src.ingestion.ingest_users - INFO - Read 428 records from users2.csv
2026-01-22 18:30:02 - src.ingestion.ingest_users - INFO - Merged dataset contains 928 total records
2026-01-22 18:30:02 - src.ingestion.ingest_users - WARNING - Found 1 duplicate user_ids in merged data
2026-01-22 18:30:03 - src.ingestion.ingest_users - INFO - ✓ User ingestion completed in 2.45 seconds
```

---

## 5. Raw Data Storage Structure

### 5.1 Data Lake Architecture

```
storage/
├── raw/                    # Raw ingested data (as-is from sources)
│   ├── users/
│   │   └── 2026-01-22/
│   │       ├── users_merged.parquet
│   │       └── users_merged_metadata.json
│   ├── products/
│   │   └── 2026-01-22/
│   │       ├── products.parquet
│   │       └── products_metadata.json
│   └── transactions/
│       └── 2026-01-22/
│           ├── transactions.parquet
│           └── transactions_metadata.json
```

### 5.2 Partitioning Strategy

**Format**: `storage/{data_layer}/{source}/{YYYY-MM-DD}/{filename}.{format}`

| Component | Description | Example |
|-----------|-------------|---------|
| data_layer | Pipeline stage | raw, validated, prepared, features |
| source | Data source name | users, products, transactions |
| YYYY-MM-DD | Date partition | 2026-01-22 |
| filename | Descriptive name | users_merged |
| format | File format | parquet, csv, json |

### 5.3 Storage Utility
**File**: `src/utils/storage.py`

```python
class DataLakeStorage:
    """Manages data lake storage with partitioning and metadata"""
    
    def save_dataframe(self, df, source, data_type, filename, format='parquet'):
        """Save dataframe to partitioned storage with metadata"""
        
    def load_latest(self, source, data_type, format='parquet'):
        """Load most recent data from storage"""
```

---

## 6. Metadata Generation

### 6.1 Metadata Schema
Each data file has an accompanying `_metadata.json`:

```json
{
  "source": "users",
  "data_type": "raw",
  "timestamp": "2026-01-22T18:30:00",
  "file_path": "storage/raw/users/2026-01-22/users_merged.parquet",
  "file_size_bytes": 45678,
  "record_count": 927,
  "schema": {
    "columns": ["user_id", "age", "gender", "device"],
    "dtypes": {
      "user_id": "int64",
      "age": "float64",
      "gender": "object",
      "device": "object"
    }
  },
  "checksum_md5": "abc123def456...",
  "null_counts": {
    "user_id": 0,
    "age": 5,
    "gender": 2,
    "device": 3
  },
  "memory_usage_bytes": 74256
}
```

### 6.2 Checksum Calculation
MD5 checksums ensure data integrity:

```python
def _calculate_checksum(self, file_path: Path) -> str:
    """Calculate MD5 checksum of file"""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
```

---

## 7. File Archive System

### 7.1 Archive Directory
Processed source files are moved to `raw/archive/`:

```
raw/
├── archive/
│   ├── users1_20260122_183000.csv
│   ├── users2_20260122_183000.csv
│   ├── products_20260122_183500.json
│   └── transactions_20260122_184000.csv
```

### 7.2 Archive Logic

```python
def archive_processed_files(self, processed_paths: List[Path]):
    """Move processed source files to archive directory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for source_path in processed_paths:
        archive_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
        dest_path = self.archive_dir / archive_filename
        shutil.move(str(source_path), str(dest_path))
        logger.info(f"Archived {source_path.name} to {dest_path}")
```

---

## 8. Running the Ingestion Pipeline

### 8.1 Individual Scripts
```bash
# Ingest users
python -m src.ingestion.ingest_users

# Ingest products
python -m src.ingestion.ingest_products

# Ingest transactions
python -m src.ingestion.ingest_transactions
```

### 8.2 All Ingestion (Orchestrated)
```bash
# Via Prefect flow
python src/orchestration/prefect_flow.py --mode run --flow ingestion
```

### 8.3 Complete Pipeline
```bash
# Run full pipeline
python run_pipeline.py
```

---

## 9. Ingestion Results Summary

| Dataset | Records | File Size | Format | Status |
|---------|---------|-----------|--------|--------|
| Users | 927 | ~45 KB | Parquet | ✅ Ingested |
| Products | 101 | ~12 KB | Parquet | ✅ Ingested |
| Transactions | 3,001 | ~120 KB | Parquet | ✅ Ingested |

---

## 10. Configuration

### 10.1 Config File
**File**: `src/config.json`

```json
{
    "data_dir": "raw",
    "storage_base": "storage",
    "products_file": "products.json",
    "interactions_file": "interactions.json",
    "users_file": "users.json",
    "schedules": {
        "ingestion_flow": {
            "enabled": true,
            "cron": "0 6 * * *",
            "description": "Daily at 6:00 AM"
        }
    }
}
```

---

## Deliverables Checklist

| Deliverable | Status | Location |
|-------------|--------|----------|
| Python scripts for ingestion | ✅ | `src/ingestion/` |
| Logs showing ingestion success/failure | ✅ | `logs/` |
| Folder/bucket structure for raw data | ✅ | `storage/raw/` |
| Storage structure documentation | ✅ | `docs/STORAGE_STRUCTURE.md` |
| Upload scripts or configuration files | ✅ | `src/utils/storage.py`, `src/config.json` |
