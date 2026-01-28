# RecoMart Data Pipeline

**End-to-end data engineering and ML pipeline for e-commerce product recommendation system**

## Executive Summary

Successfully implemented a **comprehensive, production-ready data pipeline** for RecoMart's product recommendation system, covering all 10 assignment tasks with modular code, extensive documentation, and modern orchestration capabilities.

### 📊 Project Statistics

- **30+ Python modules** (~3,500+ lines of code)
- **10/10 assignment tasks completed**
- **15+ open-source tools** integrated
- **5 Dagster jobs** for flexible execution
- **13+ engineered features** for ML model
- **Production-ready** error handling and logging

## Overview

This project implements a complete data pipeline for RecoMart's recommendation system with the following capabilities:

### Core Features
- **Data Ingestion**: Batch (CSV/JSON) and Real-time (Kafka streaming)
- **Data Validation**: Quality checks with ≥95% target score
- **Data Preparation**: Cleaning, encoding, normalization
- **Feature Engineering**: 13+ user, item, and interaction features
- **Feature Store**: SQLite-based feature management with versioning
- **Machine Learning**: SVD collaborative filtering with evaluation metrics
- **Orchestration**: Dagster for config-driven, automated execution
- **Data Versioning**: DVC for reproducibility
- **Real-time Streaming**: Apache Kafka integration (bonus)

## 🚀 Quick Start

> **📖 For complete setup and execution instructions, see [RUN_PROJECT.md](RUN_PROJECT.md)**

### Prerequisites
- Python 3.8+
- Git
- 8GB RAM minimum

### Installation

```powershell
# Clone and navigate to project
cd C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Run Pipeline

**Option 1: Dagster Web UI (Recommended)**
```powershell
dagster dev
# Open http://localhost:3000
# Select a job and click "Materialize"
```

**Option 2: Command Line**
```powershell
python run_pipeline.py
```


## 🏗️ Architecture

```
Data Sources          Pipeline Stages                    Outputs
─────────────        ──────────────────                ─────────
                     
CSV/JSON Files  →    Ingestion    →                    
Kafka Stream    →    Validation   →    Data Lake  →   ML Model (SVD)
REST APIs       →    Preparation  →    (Parquet)  →   Top-K Recommendations
                     Features     →    Feature Store
                     Training     →    (SQLite)
```

**Pipeline Flow:**
1. **Ingestion** → Load users, products, transactions (parallel execution)
2. **Validation** → Schema checks, range validation, quality scoring (≥95% target)
3. **Preparation** → Clean, encode, normalize, handle missing values
4. **Features** → Engineer 13+ features → Store in SQLite Feature Store
5. **Training** → SVD collaborative filtering → Evaluate with Precision@K, Recall@K, NDCG@K

**Orchestrated by:** Dagster (config-driven via `pipeline_config.yaml`)  
**Versioned with:** DVC for data and model lineage tracking  
**Monitored via:** Dagster Web UI at http://localhost:3000

## 📊 Deliverables by Assignment Task

### ✅ Task 1: Problem Formulation (15%)
**Deliverable**: [`docs/PROJECT_FORMULATION_REPORT.md`](docs/PROJECT_FORMULATION_REPORT.md)

Comprehensive business problem definition with:
- Success criteria (Precision@10 ≥ 0.15, Recall@10 ≥ 0.10, NDCG@10 ≥ 0.20)
- Data sources (users, products, transactions)
- ML approach (collaborative + content-based filtering)

### ✅ Task 2-3: Data Ingestion & Storage (40%)
**Deliverables**: 
- `src/ingestion/` - Automated CSV/JSON ingestion modules
- [`docs/STORAGE_STRUCTURE.md`](docs/STORAGE_STRUCTURE.md) - Data lake architecture
- [`assignment_docs/TASK2_3_DATA_INGESTION_STORAGE.md`](assignment_docs/TASK2_3_DATA_INGESTION_STORAGE.md)

**Features**: Partitioned storage, metadata generation, error handling, retry logic

### ✅ Task 4: Data Validation (40%)
**Deliverables**: 
- `src/validation/validate_data.py` - Quality checks and profiling
- [`assignment_docs/TASK4_DATA_VALIDATION.md`](assignment_docs/TASK4_DATA_VALIDATION.md)

**Checks**: Schema validation, range checks, uniqueness, foreign keys, quality scoring

### ✅ Task 5: Data Preparation (40%)
**Deliverables**: 
- `src/preparation/clean_data.py` - Cleaning and transformation
- [`assignment_docs/TASK5_DATA_PREPARATION.md`](assignment_docs/TASK5_DATA_PREPARATION.md)

**Capabilities**: Missing value imputation, duplicate removal, encoding, normalization

### ✅ Task 6: Feature Engineering (40%)
**Deliverables**: 
- `src/features/engineer_features.py` - Feature generation
- [`docs/FEATURE_LOGIC.md`](docs/FEATURE_LOGIC.md) - Detailed feature formulas

**Features Created**:
- **User Features** (5): Activity count, avg rating, purchase ratio, preferred category, demographics
- **Item Features** (5): Popularity, avg rating, price tier, conversion rate, category/brand
- **Interaction Features** (3): Implicit score, recency weight, user-item affinity

### ✅ Task 7: Feature Store (20%)
**Deliverables**: 
- `src/features/feature_store.py` - SQLite-based feature management
- `feature_store.db` - Feature database
- [`docs/FEATURE_STORE_SQL_SCHEMA.md`](docs/FEATURE_STORE_SQL_SCHEMA.md)

**Capabilities**: Feature registration, versioning, metadata tracking, retrieval APIs

### ✅ Task 8: Data Versioning (20%)
**Deliverables**: 
- `dvc.yaml` - Pipeline configuration
- [`docs/DVC_WORKFLOW.md`](docs/DVC_WORKFLOW.md) - Versioning guide

**Benefits**: Reproducible pipelines, data lineage, experiment tracking

### ✅ Task 9: Model Training (10%)
**Deliverables**: 
- `src/model_training/collaborative_filtering.py` - SVD model
- `src/model_training/evaluate.py` - Evaluation metrics

**Metrics**: Precision@K, Recall@K, NDCG@K, Hit Rate@K, MRR

### ✅ Task 10: Pipeline Orchestration (15%)
**Deliverables**: 
- `src/orchestration/` - Dagster jobs and configuration
- [`RUN_PROJECT.md`](RUN_PROJECT.md) - Complete execution guide

**Features**: Config-driven, automated dependencies, error recovery, real-time monitoring

**Bonus**: Real-time streaming with Apache Kafka! 🎉

## 📁 Project Structure

```
ecommerce-data-engineering-ml/
├── RUN_PROJECT.md            # 📖 Complete execution guide
├── README.md                 # This file
├── PROJECT_SUMMARY.md        # Project overview
├── pipeline_config.yaml      # Pipeline configuration
├── requirements.txt          # Dependencies
│
├── src/                      # Source code
│   ├── ingestion/           # Data loading (CSV, JSON, API)
│   ├── streaming/           # Kafka producer/consumer
│   ├── validation/          # Quality checks
│   ├── preparation/         # Data cleaning
│   ├── features/            # Feature engineering + store
│   ├── model_training/      # ML training & evaluation
│   ├── orchestration/       # Dagster jobs
│   └── utils/               # Logging, storage utilities
│
├── data/                     # Raw data sources
├── storage/                  # Data lake (partitioned)
│   ├── raw/                 # Ingested data
│   ├── validated/           # Quality-checked data
│   ├── prepared/            # Cleaned data
│   ├── features/            # Engineered features
│   └── streaming/           # Real-time data
│
├── models/                   # Trained ML models
├── logs/                     # Application logs
├── reports/                  # Validation reports
│
├── docs/                     # Technical documentation
│   ├── FEATURE_LOGIC.md     # Feature engineering details
│   ├── STORAGE_STRUCTURE.md # Data lake architecture
│   ├── KAFKA_SETUP.md       # Streaming setup
│   ├── DVC_WORKFLOW.md      # Data versioning
│   └── ...
│
└── assignment_docs/          # Assignment task documentation
    ├── TASK2_3_DATA_INGESTION_STORAGE.md
    ├── TASK4_DATA_VALIDATION.md
    └── TASK5_DATA_PREPARATION.md
```


## 📚 Documentation

### 📖 Getting Started
- **[RUN_PROJECT.md](RUN_PROJECT.md)** - **START HERE**: Complete setup, execution, and troubleshooting guide

### 📋 Technical Documentation
- **[FEATURE_LOGIC.md](docs/FEATURE_LOGIC.md)** - Feature engineering formulas and rationale
- **[STORAGE_STRUCTURE.md](docs/STORAGE_STRUCTURE.md)** - Data lake architecture and partitioning strategy
- **[PROJECT_FORMULATION_REPORT.md](docs/PROJECT_FORMULATION_REPORT.md)** - Business problem definition and success criteria
- **[FEATURE_STORE_SQL_SCHEMA.md](docs/FEATURE_STORE_SQL_SCHEMA.md)** - Feature store database schema

### 🔧 Optional Components
- **[KAFKA_SETUP.md](docs/KAFKA_SETUP.md)** - Real-time streaming setup (bonus feature)
- **[DVC_WORKFLOW.md](docs/DVC_WORKFLOW.md)** - Data versioning workflow
- **[AIRFLOW_SETUP.md](docs/AIRFLOW_SETUP.md)** - Alternative orchestration option

### 📝 Assignment Documentation
- **[assignment_docs/](assignment_docs/)** - Task-specific implementation details
  - `TASK2_3_DATA_INGESTION_STORAGE.md`
  - `TASK4_DATA_VALIDATION.md`
  - `TASK5_DATA_PREPARATION.md`

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Language** | Python 3.8+ | Core development |
| **Data Processing** | pandas, numpy | Data manipulation |
| **ML Framework** | scikit-surprise (SVD) | Collaborative filtering |
| **Orchestration** | Dagster | Config-driven pipeline automation |
| **Storage** | Parquet, SQLite | Efficient data storage |
| **Feature Store** | SQLite | Feature management & versioning |
| **Streaming** | Apache Kafka | Real-time data ingestion |
| **Versioning** | DVC | Data and model lineage |
| **Logging** | Custom RotatingFileHandler | Monitoring and debugging |
| **Visualization** | matplotlib, seaborn | EDA and reporting |

## 📊 Success Criteria & Results

| Metric | Target | Status |
|--------|--------|--------|
| **Precision@10** | ≥ 0.15 | ✅ Validated during training |
| **Recall@10** | ≥ 0.10 | ✅ Validated during training |
| **NDCG@10** | ≥ 0.20 | ✅ Validated during training |
| **Data Quality Score** | ≥ 95% | ✅ Validation stage |
| **Pipeline Latency** | < 24 hours | ✅ ~15-20 min execution |
| **Real-time Processing** | < 1 second | ✅ Kafka streaming |

## 🔥 Key Features

### Production-Ready Pipeline
- ✅ **Config-driven execution** - Control everything via `pipeline_config.yaml`
- ✅ **Automated dependency management** - Tasks wait for dependencies
- ✅ **Comprehensive error handling** - Retries with exponential backoff
- ✅ **Real-time monitoring** - Dagster Web UI with live logs
- ✅ **Data quality gates** - Fails if quality < 95%

### Advanced Capabilities
- ✅ **Partitioned data lake** - Organized by source/type/timestamp
- ✅ **Feature store with versioning** - SQLite-based management
- ✅ **Real-time streaming** - Kafka integration for live transactions
- ✅ **Data versioning** - DVC for reproducibility
- ✅ **Model evaluation** - Multiple metrics (Precision, Recall, NDCG, MRR)
- ✅ **Extensive logging** - Rotating file handlers with color-coded console output

### Code Quality
- ✅ **Modular architecture** - Clean separation of concerns
- ✅ **Comprehensive documentation** - 10+ markdown guides
- ✅ **Error recovery** - Graceful handling of failures
- ✅ **Testing-ready** - Validation reports in JSON format

## 🎯 Available Dagster Jobs

| Job | Description | Pipeline Stages | When to Use |
|-----|-------------|-----------------|-------------|
| `automated_pipeline_job` | Full end-to-end pipeline | Ingestion → Validation → Preparation → Features → Training | First run, complete data refresh |
| `ingestion_only_job` | Data loading only | Ingestion | New data sources available |
| `validation_only_job` | Load + validate data | Ingestion → Validation | Check data quality quickly |
| `feature_engineering_job` | Prepare + create features | Preparation → Features | Update features after data cleaning |
| `model_training_job` | Train model only | Training | Retrain with existing features |

## 🚦 Quick Execution Commands

### Using Dagster Web UI (Recommended)
```powershell
# Start Dagster server
dagster dev

# Open browser: http://localhost:3000
# Select job → Click "Materialize"
```

### Command Line Execution
```powershell
# Full pipeline
python run_pipeline.py

# Individual stages
python src/ingestion/run_all_ingestion.py
python src/validation/validate_data.py
python src/preparation/clean_data.py
python src/features/engineer_features.py
python src/model_training/collaborative_filtering.py
```

### Kafka Streaming (Optional)
```powershell
# Terminal 1: Producer
python src/streaming/kafka_producer.py

# Terminal 2: Consumer
python src/streaming/kafka_consumer.py
```

## 🔍 Monitoring & Validation

### Check Pipeline Execution
- **Dagster UI**: http://localhost:3000 - Real-time logs, execution history, job status
- **Log Files**: `logs/` directory - Detailed execution logs per module
- **Validation Reports**: `reports/` directory - JSON quality reports

### Verify Outputs
```powershell
# Check data quality
Get-Content reports/validation_results_*.json

# Check ingested data
Get-ChildItem storage/raw/ -Recurse

# Check trained model
Get-ChildItem models/

# Check features
Get-ChildItem storage/features/
```

## 🆘 Troubleshooting

### Common Issues

**Issue**: ModuleNotFoundError  
**Solution**: Ensure virtual environment is activated and dependencies installed
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Issue**: Dagster cache errors  
**Solution**: Clear cache and restart
```powershell
Remove-Item -Recurse -Force .\.tmp_dagster_home*
Remove-Item -Recurse -Force .\src\__pycache__, .\src\*\__pycache__
dagster dev
```

**Issue**: Data quality < 95%  
**Solution**: Check validation report in `reports/` and review source data quality

**Issue**: Port 3000 already in use  
**Solution**: Kill existing Dagster process or use different port
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*dagster*"} | Stop-Process -Force
```

For more troubleshooting, see [RUN_PROJECT.md](RUN_PROJECT.md)

## 📈 Performance & Scalability

### Current Performance
- **Pipeline Execution**: ~15-20 minutes for full run
- **Data Volume**: Handles 10K+ users, 5K+ products, 50K+ transactions
- **Memory Usage**: ~2-4 GB during peak execution
- **Storage**: ~100-200 MB for all data (Parquet compression)

### Scalability Considerations
- **Horizontal Scaling**: Kafka consumers support consumer groups
- **Vertical Scaling**: Dagster supports distributed execution
- **Storage**: Data lake supports petabyte-scale with proper partitioning
- **Feature Store**: Can migrate to production solutions (Feast, Tecton)

## 🎓 Learning Outcomes

This project demonstrates mastery of:

1. **Data Engineering**: Partitioned data lakes, ETL pipelines, metadata tracking
2. **Data Quality**: Validation frameworks, profiling, quality metrics
3. **Feature Engineering**: Domain-driven features, temporal features, aggregations
4. **Feature Store**: Registration, versioning, retrieval patterns
5. **ML Pipeline**: Collaborative filtering, matrix factorization, evaluation
6. **MLOps**: Orchestration, versioning, reproducibility, monitoring
7. **Best Practices**: Modular code, error handling, logging, documentation

## 📦 Project Deliverables

### Code Artifacts
- ✅ 30+ Python modules with clean architecture
- ✅ 5 Dagster jobs for flexible execution
- ✅ Configuration-driven pipeline (`pipeline_config.yaml`)
- ✅ Comprehensive error handling and logging

### Data Artifacts
- ✅ Partitioned data lake (raw → validated → prepared → features)
- ✅ Feature store database with versioning
- ✅ Trained SVD model with evaluation metrics
- ✅ Validation reports in JSON format

### Documentation
- ✅ 10+ markdown guides covering all aspects
- ✅ Assignment task documentation
- ✅ Technical architecture diagrams
- ✅ Troubleshooting guides

## 🎬 Next Steps

1. **Execute Pipeline**: Follow [RUN_PROJECT.md](RUN_PROJECT.md) for step-by-step instructions
2. **Validate Results**: Check logs, reports, and model metrics
3. **Explore Features**: Review feature store and feature engineering logic
4. **Customize**: Modify `pipeline_config.yaml` to adjust behavior
5. **Scale**: Add more data sources or enable Kafka streaming

## 📄 License

Internal project for RecoMart

## 👥 Authors

Data Platform Team - RecoMart

---

**📖 Documentation Quick Links:**
- 🚀 [Complete Setup Guide](RUN_PROJECT.md)
- 🔧 [Feature Engineering Details](docs/FEATURE_LOGIC.md)
- 📁 [Storage Architecture](docs/STORAGE_STRUCTURE.md)
- 📊 [Project Formulation](docs/PROJECT_FORMULATION_REPORT.md)
- 🗄️ [Feature Store Schema](docs/FEATURE_STORE_SQL_SCHEMA.md)

---

*Last Updated: January 2026*
