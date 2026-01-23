# DVC Configuration and Setup Guide

## Overview

Data Version Control (DVC) enables versioning of datasets and models alongside code in Git, similar to Git LFS but optimized for ML workflows.

## Setup Instructions

### 1. Initialize DVC

```bash
# Initialize DVC in the repository
dvc init

# This creates .dvc directory and .dvcignore file
```

### 2. Configure Local Remote Storage

```bash
# Create local storage directory for DVC cache
mkdir -p .dvc/cache

# Add local remote (for demonstration purposes)
dvc remote add -d local .dvc/cache

# For cloud storage (AWS S3 example):
# dvc remote add -d myremote s3://my-bucket/dvc-storage
```

### 3. Track Data Files

```bash
# Track raw data
dvc add data/users1.csv
dvc add data/users2.csv
dvc add data/products.json
dvc add data/transactions.csv

# Track processed data
dvc add storage/prepared/
dvc add storage/features/

# Track models
dvc add models/
```

### 4. Commit DVC Files to Git

```bash
# Add .dvc files to Git
git add data/*.dvc storage/*.dvc models/*.dvc .dvc/.gitignore .dvc/config

# Commit
git commit -m "Add data and model versioning with DVC"
```

### 5. Push Data to Remote

```bash
# Push tracked data to DVC remote
dvc push
```

## DVC Pipeline

Create `dvc.yaml` to define reproducible pipeline:

```yaml
stages:
  ingest:
    cmd: python src/ingestion/run_all_ingestion.py
    deps:
      - data/users1.csv
      - data/users2.csv
      - data/products.json
      - data/transactions.csv
    outs:
      - storage/raw/

  prepare:
    cmd: python src/preparation/clean_data.py
    deps:
      - storage/raw/
      - src/preparation/clean_data.py
    outs:
      - storage/prepared/

  features:
    cmd: python src/features/engineer_features.py
    deps:
      - storage/prepared/
      - src/features/engineer_features.py
    outs:
      - storage/features/

  train:
    cmd: python src/models/collaborative_filtering.py
    deps:
      - storage/features/
      - src/models/collaborative_filtering.py
    outs:
      - models/collaborative_filtering.pkl
    metrics:
      - metrics.json:
          cache: false
```

## Usage

### Run Pipeline

```bash
# Run entire pipeline
dvc repro

# Run specific stage
dvc repro features
```

### Version Management

```bash
# Create new version
git add .
git commit -m "Update model with new features"
dvc push

# Checkout old version
git checkout <commit-hash>
dvc checkout
```

### Pull Data

```bash
# Pull data from remote (when cloning repo)
git clone <repo-url>
dvc pull
```

## Data Lineage

DVC tracks:
- **Input files**: Raw datasets
- **Code**: Python scripts
- **Output files**: Processed data, models
- **Metrics**: Performance metrics

### View DAG

```bash
# Visualize pipeline
dvc dag
```

Output:
```
         +--------+
         | ingest |
         +--------+
              *
              *
              *
         +---------+
         | prepare |
         +---------+
              *
              *
              *
        +----------+
        | features |
        +----------+
              *
              *
              *
          +-------+
          | train |
          +-------+
```

## Metadata Tracking

DVC automatically tracks:
- File checksums (MD5)
- File sizes
- Timestamps
- Dependencies
- Pipeline stages

Access metadata:
```bash
# Show file info
dvc list . storage/features/
```

## Best Practices

1. **Track at appropriate granularity**: Don't track individual small files
2. **Use descriptive commit messages**: Explain what changed and why
3. **Push regularly**: Keep remote storage in sync
4. **Version data with code**: Tag releases together
5. **Document transformations**: Include metadata about processing

## Benefits for RecoMart

- **Reproducibility**: Recreate any version of the model
- **Collaboration**: Share data without bloating Git repo
- **Experimentation**: Branch/merge data like code
- **Audit trail**: Complete lineage from raw to model
- **Storage efficiency**: Deduplication and compression

## Directory Structure with DVC

```
ecommerce-data-engineering-ml/
├── .dvc/
│   ├── config              # DVC configuration
│   ├── .gitignore          # Files to ignore in Git
│   └── cache/              # Local DVC cache
├── data/
│   ├── users1.csv.dvc      # DVC metadata file
│   ├── users2.csv.dvc
│   ├── products.json.dvc
│   └── transactions.csv.dvc
├── storage/
│   ├── prepared.dvc        # Tracks directory
│   └── features.dvc
├── models/
│   └── collaborative_filtering.pkl.dvc
├── dvc.yaml                # Pipeline definition
├── dvc.lock                # Pipeline execution state
└── .dvcignore              # DVC ignore patterns
```

## Troubleshooting

### Issue: Large files slow Git
**Solution**: Ensure DVC is tracking them (check .dvc files exist)

### Issue: Out of sync
**Solution**: 
```bash
dvc status    # Check status
dvc checkout  # Restore from cache
dvc pull      # Pull from remote
```

### Issue: Corrupted cache
**Solution**:
```bash
dvc cache clear
dvc pull -f  # Force pull
```

## Alternative: Git LFS

For simpler needs, Git LFS can be used:
```bash
git lfs install
git lfs track "*.csv" "*.parquet" "*.pkl"
git add .gitattributes
```

However, DVC is preferred for ML because:
- Better for large datasets
- Pipeline support
- Metrics tracking
- Cloud storage integration
