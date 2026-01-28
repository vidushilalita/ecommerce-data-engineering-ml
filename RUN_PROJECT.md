# 🚀 RecoMart E-Commerce Data Engineering & ML Project - Setup & Execution Guide

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Running the Pipeline](#running-the-pipeline)
- [Available Jobs](#available-jobs)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Software
- **Python 3.12** (recommended) or Python 3.8+
- **Git** (for version control)
- **VS Code** (recommended IDE)

### System Requirements
- **OS**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: At least 2GB free

---

## 📦 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/vidushilalita/ecommerce-data-engineering-ml.git
cd ecommerce-data-engineering-ml
```

### Step 2: Create Virtual Environment
```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
# Check Python version
python --version

# Check if Dagster is installed
dagster --version
```

---

## 📂 Project Structure

```
ecommerce-data-engineering-ml/
├── data/                          # Raw input data files
├── storage/                       # Data lake storage
│   ├── raw/                      # Ingested raw data
│   ├── validated/                # Validated data
│   ├── prepared/                 # Cleaned & prepared data
│   └── features/                 # Engineered features
├── models/                        # Trained ML models
├── logs/                          # Application logs
├── reports/                       # Validation reports
├── src/                          # Source code
│   ├── ingestion/               # Data ingestion modules
│   ├── validation/              # Data validation
│   ├── preparation/             # Data cleaning
│   ├── features/                # Feature engineering
│   ├── model_training/          # ML model training
│   ├── orchestration/           # Dagster pipelines
│   └── utils/                   # Utility functions
├── pipeline_config.yaml          # Pipeline configuration
└── requirements.txt              # Python dependencies
```

---

## 🎯 Running the Pipeline

### Option 1: Using Dagster UI (Recommended)

#### 1. Start Dagster Server
```bash
# Activate virtual environment first
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Start Dagster development server
dagster dev -m src.orchestration.repository
```

#### 2. Access Dagster UI
- Open browser: **http://127.0.0.1:3000**
- You'll see the Dagster web interface with all available jobs

#### 3. Run a Job
1. Click on **"Jobs"** in the left sidebar
2. Select the job you want to run (e.g., `automated_pipeline_job`)
3. Click **"Launch Run"** button
4. Monitor execution in real-time

### Option 2: Using Command Line

#### Run Complete Pipeline
```bash
python run_dagster_pipeline.py
```

#### Run Specific Components
```bash
# Data Ingestion Only
python src/ingestion/ingest_users.py
python src/ingestion/ingest_products.py
python src/ingestion/ingest_transactions.py

# Data Validation
python src/validation/validate_data.py

# Data Preparation
python src/preparation/clean_data.py

# Feature Engineering
python src/features/engineer_features.py

# Model Training
python src/model_training/collaborative_filtering.py
```

---

## 🎨 Available Jobs

### 1. ⭐ **automated_pipeline_job** (Recommended)
**Full end-to-end pipeline with all stages**

```yaml
Pipeline Stages:
1. Data Ingestion (Users, Products, Transactions)
2. Data Validation (Quality checks)
3. Data Preparation (Cleaning & transformation)
4. Feature Engineering (ML features)
5. Model Training (Collaborative Filtering)
```

**When to use**: 
- First-time setup
- Complete pipeline execution
- Production deployments

**Expected Runtime**: 5-10 minutes

---

### 2. 📥 **ingestion_only_job**
**Ingest data from raw files into data lake**

**What it does**:
- Reads CSV/JSON files from `data/` directory
- Merges and deduplicates data
- Stores in `storage/raw/`

**When to use**:
- New data arrives
- Data refresh needed
- Testing ingestion logic

**Expected Runtime**: 30-60 seconds

---

### 3. ✅ **validation_only_job**
**Validate data quality and generate reports**

**What it does**:
- Runs data quality checks
- Validates completeness, correctness, consistency
- Generates JSON reports in `reports/`

**When to use**:
- After ingestion
- Quality assessment
- Debugging data issues

**Expected Runtime**: 20-40 seconds

**Prerequisites**: Data must be ingested first

---

### 4. 🔧 **feature_engineering_job**
**Data preparation + feature engineering**

**What it does**:
- Cleans data (handles missing values, encodes categories)
- Engineers ML features (user, item, interaction features)
- Stores in `storage/prepared/` and `storage/features/`

**When to use**:
- After validation
- Before model training
- Feature updates/improvements

**Expected Runtime**: 1-2 minutes

**Prerequisites**: Validated data must exist

---

### 5. 🤖 **model_training_job**
**Train collaborative filtering model**

**What it does**:
- Loads engineered features
- Trains SVD-based recommendation model
- Saves model to `models/collaborative_filtering.pkl`

**When to use**:
- After feature engineering
- Model retraining
- Hyperparameter tuning

**Expected Runtime**: 30-60 seconds

**Prerequisites**: Features must be engineered first

---

## ⚙️ Configuration

### Modify Pipeline Settings
Edit `pipeline_config.yaml` to customize:

```yaml
# Example: Change model hyperparameters
tasks:
  training:
    config:
      svd:
        n_factors: 100        # Increase for better accuracy
        n_epochs: 30          # More training iterations
        learning_rate: 0.001  # Adjust learning speed
```

### Enable/Disable Tasks
```yaml
tasks:
  ingestion:
    enabled: true   # Set to false to skip
  validation:
    enabled: true
  # ... etc
```

---

## 🔍 Monitoring & Logs

### View Logs
```bash
# Application logs
ls logs/

# View specific log file
cat logs/src_ingestion_ingest_users.log
```

### Dagster UI Monitoring
- **Run Status**: Green (Success), Red (Failed), Yellow (In Progress)
- **Execution Time**: View duration for each step
- **Logs**: Click on any step to see detailed logs
- **Outputs**: View data outputs and metadata

---

## 📊 Outputs

### Data Outputs
```
storage/
├── raw/                    # Raw ingested data
│   ├── users.parquet
│   ├── products.parquet
│   └── transactions.parquet
├── validated/              # Validated data
├── prepared/               # Clean data
│   ├── users_prepared.parquet
│   ├── products_prepared.parquet
│   └── transactions_prepared.parquet
└── features/               # ML features
    ├── user_features.parquet
    ├── item_features.parquet
    └── interaction_features.parquet
```

### Model Outputs
```
models/
└── collaborative_filtering.pkl   # Trained recommendation model
```

### Reports
```
reports/
└── validation_results_<timestamp>.json   # Data quality reports
```

---

## 🐛 Troubleshooting

### Issue: Python version mismatch
```bash
# Check Python version
python --version

# Should be Python 3.8 or higher
```

### Issue: Module not found errors
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue: Dagster port already in use
```bash
# Kill existing Dagster processes (Windows)
Get-Process | Where-Object {$_.ProcessName -like "*dagster*"} | Stop-Process -Force

# Kill existing Dagster processes (macOS/Linux)
pkill -f dagster
```

### Issue: ANSI color codes in logs
**Fixed!** The logger has been updated to remove color codes from log files while keeping them in console output.

### Issue: Dagster configuration errors
```bash
# Remove old configuration and cache
Remove-Item dagster.yaml -Force
Remove-Item -Path ".tmp_dagster_home*" -Recurse -Force
Remove-Item -Path "src\__pycache__" -Recurse -Force
```

### Issue: Data files not found
Ensure your data files are in the `data/` directory:
- `users1.csv`, `users2.csv` (or any file with 'user' in name)
- `products.json`
- `transactions.csv` (or any file with 'transaction' in name)

### Issue: Model training fails
**Error**: `TypeError: object of type 'generator' has no len()`
**Solution**: Already fixed! Use `trainset.n_ratings` instead of `len(trainset.all_ratings())`

---

## 🔄 Clean Restart

If you need a fresh start:

```bash
# Windows PowerShell
Get-Process | Where-Object {$_.ProcessName -like "*dagster*"} | Stop-Process -Force
Remove-Item -Path "src\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "src\orchestration\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".tmp_dagster_home*" -Recurse -Force -ErrorAction SilentlyContinue
dagster dev -m src.orchestration.repository

# macOS/Linux
pkill -f dagster
find . -type d -name "__pycache__" -exec rm -rf {} +
rm -rf .tmp_dagster_home*
dagster dev -m src.orchestration.repository
```

---

## 🎓 Execution Order

For first-time setup, run jobs in this order:

```
1. automated_pipeline_job (Complete pipeline)
   OR run individual jobs:
   
2. ingestion_only_job
   ↓
3. validation_only_job
   ↓
4. feature_engineering_job
   ↓
5. model_training_job
```

---

## 📈 Performance Tips

1. **Use automated_pipeline_job** for production deployments
2. **Monitor logs** in `logs/` directory for issues
3. **Check validation reports** before proceeding to next steps
4. **Adjust timeouts** in `pipeline_config.yaml` for large datasets
5. **Clear cache** periodically to avoid stale data issues

---

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check `docs/` folder for detailed documentation
- **Logs**: Review logs in `logs/` directory for debugging

---

## ✅ Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Data files present in `data/` directory
- [ ] Dagster server started (`dagster dev -m src.orchestration.repository`)
- [ ] Browser opened to http://127.0.0.1:3000
- [ ] First pipeline run completed successfully

---

## 🎉 Success Indicators

Your pipeline is working correctly if:

✅ Dagster UI shows all 5 jobs  
✅ Data files appear in `storage/` subdirectories  
✅ Validation reports generated in `reports/`  
✅ Model file created in `models/collaborative_filtering.pkl`  
✅ No errors in logs  
✅ All job runs show green (success) status  

---

**Happy Data Engineering! 🚀**
