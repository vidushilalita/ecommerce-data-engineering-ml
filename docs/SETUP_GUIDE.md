# RecoMart Data Pipeline - Setup Guide

## Quick Start (5 Minutes)

### 1. Environment Setup

```powershell
# Navigate to project directory
cd C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Complete Pipeline

```powershell
# Execute end-to-end pipeline
python run_pipeline.py
```

This will run all 5 stages:
1. ✓ Data Ingestion
2. ✓ Data Validation  
3. ✓ Data Preparation
4. ✓ Feature Engineering
5. ✓ Model Training

---

## Step-by-Step Execution

### Stage 1: Data Ingestion

```powershell
python src/ingestion/run_all_ingestion.py
```

**Output**:
- `storage/raw/users/` - Merged user data
- `storage/raw/products/` - Product catalog
- `storage/raw/transactions/` - User interactions

### Stage 2: Data Validation

```powershell
python src/validation/validate_data.py
```

**Output**:
- `reports/validation_results_*.json` - Quality metrics
- Target: Data Quality Score ≥ 95%

### Stage 3: Data Preparation

```powershell  
python src/preparation/clean_data.py
```

**Output**:
- `storage/prepared/users_clean.parquet`
- `storage/prepared/products_clean.parquet`
- `storage/prepared/transactions_clean.parquet`

### Stage 4: Feature Engineering

```powershell
python src/features/engineer_features.py
```

**Output**:
- `storage/features/user_features.parquet`
- `storage/features/item_features.parquet`
- `storage/features/interaction_features.parquet`

### Stage 5: Feature Store Setup

```powershell
python src/features/feature_store.py
```

**Output**:
- `feature_store.db` - SQLite feature store
- `docs/feature_metadata.json` - Feature catalog

### Stage 6: Model Training

```powershell
python src/models/collaborative_filtering.py
```

**Output**:
- `models/collaborative_filtering.pkl` - Trained SVD model

---

## Advanced: Apache Airflow Setup

### 1. Set Airflow Home

```powershell
# Set environment variable
$env:AIRFLOW_HOME = "C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml\airflow"
[System.Environment]::SetEnvironmentVariable('AIRFLOW_HOME', $env:AIRFLOW_HOME, 'User')
```

### 2. Initialize Airflow

```powershell
# Initialize database
airflow db init

# Create admin user
airflow users create `
    --username admin `
    --firstname Admin `
    --lastname User `
    --role Admin `
    --email admin@recomart.com `
    --password admin123
```

### 3. Start Airflow (Two Terminals)

**Terminal 1 - Webserver:**
```powershell
airflow webserver --port 8080
```

**Terminal 2 - Scheduler:**
```powershell
airflow scheduler
```

### 4. Access UI

Open browser: http://localhost:8080
- Username: admin
- Password: admin123

### 5. Trigger Pipeline

In Airflow UI:
1. Find DAG: `recomart_end_to_end_pipeline`
2. Click "Trigger DAG" button
3. Monitor execution in Graph/Tree view

---

## Advanced: DVC Setup

### 1. Initialize DVC

```powershell
# Initialize DVC
dvc init

# Configure local remote
dvc remote add -d local .dvc/cache
```

### 2. Track Data

```powershell
# Track raw data
dvc add data/users1.csv
dvc add data/users2.csv
dvc add data/products.json
dvc add data/transactions.csv

# Commit to Git
git add data/*.dvc .dvc/.gitignore
git commit -m "Add data versioning"
```

### 3. Run DVC Pipeline

```powershell
# Execute pipeline with DVC
dvc repro

# View pipeline DAG
dvc dag
```

---

## Verification

### Check Pipeline Outputs

```powershell
# List storage contents
ls storage/raw/
ls storage/prepared/
ls storage/features/
ls models/

# Verify feature store
python -c "import sqlite3; conn = sqlite3.connect('feature_store.db'); print(conn.execute('SELECT COUNT(*) FROM user_features').fetchone())"
```

### Validate Metrics

Check that metrics meet targets:
- ✓ Data Quality Score ≥ 95%
- ✓ User features: ~927 records
- ✓ Product features: ~101 records
- ✓ Transaction features: ~3,001 records

---

## Logs and Debugging

### View Logs

```powershell
# Application logs
ls logs/

# Airflow logs  
ls airflow/logs/

# Read specific log
Get-Content logs/src_ingestion_run_all_ingestion.log -Tail 50
```

### Common Issues

**Issue: Module not found**
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: File not found errors**
```powershell
# Verify data files exist
ls data/
```

**Issue: Permission errors**
```powershell
# Run PowerShell as Administrator
# Or adjust execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Project Structure

```
ecommerce-data-engineering-ml/
├── data/                   # Raw data sources
├── storage/                # Data lake (partitioned)
│   ├── raw/               # Ingested data
│   ├── prepared/          # Cleaned data  
│   └── features/          # Engineered features
├── src/                   # Source code
│   ├── ingestion/        # Data ingestion
│   ├── validation/       # Quality checks
│   ├── preparation/      # Data cleaning
│   ├── features/         # Feature engineering
│   ├── models/           # ML models
│   └── utils/            # Common utilities
├── airflow/              # Airflow DAGs
├── models/               # Saved models
├── logs/                 # Application logs
├── docs/                 # Documentation
├── run_pipeline.py       # Master pipeline script
└── requirements.txt      # Python dependencies
```

---

## Next Steps

1. **Explore Features**: Check `docs/FEATURE_LOGIC.md`
2. **Run Airflow**: Follow `docs/AIRFLOW_SETUP.md`
3. **Version Data**: See `docs/DVC_WORKFLOW.md`
4. **Customize Models**: Edit `src/models/collaborative_filtering.py`

---

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review documentation in `docs/`
- See `docs/PROJECT_FORMULATION_REPORT.md` for details

---

## Assignment Deliverables

✅ **Task 1**: Problem Formulation - `docs/PROJECT_FORMULATION_REPORT.md`
✅ **Task 2**: Data Ingestion - `src/ingestion/`
✅ **Task 3**: Data Storage - `storage/` with partitioning
✅ **Task 4**: Data Validation - `src/validation/`
✅ **Task 5**: Data Preparation - `src/preparation/` + EDA
✅ **Task 6**: Feature Engineering - `src/features/`
✅ **Task 7**: Feature Store - `feature_store.db`
✅ **Task 8**: Data Versioning - `dvc.yaml`, DVC workflow
✅ **Task 9**: Model Training - `src/models/`
✅ **Task 10**: Orchestration - `airflow/dags/`

All 10 tasks completed! 🎉
