# RecoMart Data Lake - Storage Structure Documentation

## Overview

The RecoMart data pipeline uses a structured data lake approach with partitioning by source, data layer, and timestamp. All data is stored in the `storage/` directory.

## Directory Structure

```
storage/
├── raw/                     # Raw ingested data (as-is from sources)                   
│   ├── users/
│   │   └── YYYY-MM-DD/
│   │       ├── users_merged.parquet
│   │       └── users_merged_metadata.json
│   ├── products/
│   │   └── YYYY-MM-DD/
│   │       ├── products.parquet
│   │       └── products_metadata.json
│   └── transactions/
│       └── YYYY-MM-DD/
│           ├── transactions.parquet
│           └── transactions_metadata.json
├── prepared/               # Cleaned and preprocessed data               
│   ├── users/
│   │   └── YYYY-MM-DD/
│   │       ├── users_merged.parquet
│   │       └── users_merged_metadata.json
│   ├── products/
│   │   └── YYYY-MM-DD/
│   │       ├── products.parquet
│   │       └── products_metadata.json
│   └── transactions/
│       └── YYYY-MM-DD/
│           ├── transactions.parquet
│           └── transactions_metadata.json
└── features/               # Engineered features               
    ├── user_features/
    │   └── YYYY-MM-DD/
    │       ├── user_features.parquet
    │       └── user_features_metadata.json
    ├── item_features/
    │   └── YYYY-MM-DD/
    │       ├── item_features.parquet
    │       └── item_features_metadata.json
    └── interaction_features/
        └── YYYY-MM-DD/
            ├── interaction_features.parquet
            └── interaction_features_metadata.json

```

## Partitioning Strategy

### Format
```
storage/{data_layer}/{source}/{YYYY-MM-DD}/{filename}.{format}
```

### Components
- **data_layer**: Stage in pipeline (raw, prepared, features)
- **source**: Data source name (users, products, transactions)
- **YYYY-MM-DD**: Date partition for temporal organization
- **filename**: Descriptive name for the dataset
- **format**: File format (parquet, json)

## File Formats

### Parquet (Primary)
- **Usage**: Default storage format for all processed data
- **Benefits**: 
  - Columnar storage for efficient queries
  - Built-in compression
  - Schema preservation
  - Fast read/write performance

### JSON
- **Usage**: Metadata files, configuration
- **Use cases**: Lineage tracking, schema documentation

## Metadata Files

Each data file has an accompanying metadata JSON file with `_metadata` suffix.

### Metadata Schema
```json
{
  "source": "users",
  "data_type": "raw",
  "timestamp": "2026-01-22T18:30:00",
  "file_path": "storage/raw/users/2026-01-22/users_merged.parquet",
  "file_size_bytes": 123456,
  "record_count": 927,
  "schema": {
    "columns": ["user_id", "age", "gender", "device"],
    "dtypes": {
      "user_id": "int64",
      "age": "int64",
      "gender": "object",
      "device": "object"
    }
  },
  "checksum_md5": "abc123...",
  "null_counts": {
    "user_id": 0,
    "age": 5,
    "gender": 2,
    "device": 0
  },
  "memory_usage_bytes": 98765
}
```

## Data Lineage

### Tracking
Each ingestion/transformation operation generates metadata including:
- Source file location
- Processing timestamp
- Schema information
- Data quality metrics (null counts, duplicates)
- File checksum for integrity verification

### Versioning
- Date-based partitions enable temporal versioning
- Multiple versions can coexist in different date partitions
- Latest version retrieved by sorting partitions descending
