# RecoMart Data Lake - Storage Structure Documentation

## Overview

The RecoMart data pipeline uses a structured data lake approach with partitioning by source, data layer, and timestamp. All data is stored in the `storage/` directory.

## Directory Structure

```
storage/
├── raw/                    # Raw ingested data (as-is from sources)
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
├── validated/              # Post-validation data
│   ├── users/
│   ├── products/
│   └── transactions/
├── prepared/               # Cleaned and preprocessed data
│   ├── users/
│   ├── products/
│   └── transactions/
└── features/               # Engineered features
    ├── user_features/
    ├── item_features/
    └── interaction_features/
```

## Partitioning Strategy

### Format
```
storage/{data_layer}/{source}/{YYYY-MM-DD}/{filename}.{format}
```

### Components
- **data_layer**: Stage in pipeline (raw, validated, prepared, features)
- **source**: Data source name (users, products, transactions)
- **YYYY-MM-DD**: Date partition for temporal organization
- **filename**: Descriptive name for the dataset
- **format**: File format (parquet, csv, json)

### Example Paths
```
storage/raw/users/2026-01-22/users_merged.parquet
storage/validated/products/2026-01-22/products_clean.parquet
storage/prepared/transactions/2026-01-22/transactions_processed.parquet
storage/features/user_features/2026-01-22/user_features_v1.parquet
```

## File Formats

### Parquet (Primary)
- **Usage**: Default storage format for all processed data
- **Benefits**: 
  - Columnar storage for efficient queries
  - Built-in compression
  - Schema preservation
  - Fast read/write performance

### CSV
- **Usage**: Raw data input/output, human-readable exports
- **Use cases**: Data exchange, manual inspection

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

## Access Patterns

### Write Operations
```python
from src.utils.storage import DataLakeStorage

storage = DataLakeStorage()
metadata = storage.save_dataframe(
    df=dataframe,
    source='users',
    data_type='raw',
    filename='users_merged',
    format='parquet'
)
```

### Read Operations
```python
# Load latest data
df = storage.load_latest(
    source='users',
    data_type='raw',
    format='parquet'
)
```

## Best Practices

1. **Always use partitioning**: Enables efficient data management and retrieval
2. **Generate metadata**: Track lineage and quality metrics
3. **Use Parquet** for processed data: Better performance than CSV/JSON
4. **Never modify raw data**: Keep immutable raw layer
5. **Document transformations**: Include transformation logic in metadata

## Benefits

- **Scalability**: Partitioning supports growing data volumes
- **Reproducibility**: Metadata and versioning enable replay
- **Auditability**: Complete lineage from raw to features
- **Performance**: Optimized formats and columnar storage
- **Flexibility**: Support for multiple data layers and formats
