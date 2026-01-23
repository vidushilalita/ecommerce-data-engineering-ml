# RecoMart Data Pipeline

End-to-end data management pipeline for product recommendation system with **real-time streaming capabilities**.

## Overview

This project implements a comprehensive data pipeline for RecoMart's e-commerce recommendation system, covering:
- **Data Ingestion**: Batch (CSV/JSON) and Real-time (Kafka streaming)
- **Data Validation**: Quality checks and profiling
- **Data Preparation**: Cleaning, encoding, normalization
- **Feature Engineering**: User, item, and interaction features
- **Feature Store**: SQLite-based feature management
- **Machine Learning**: Collaborative filtering with SVD
- **Orchestration**: Apache Airflow DAGs
- **Streaming**: Apache Kafka for real-time transactions

## 🚀 Quick Start

### 1. Setup Environment

```powershell
# Navigate to project
cd C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Batch Pipeline

```powershell
# Execute complete pipeline
python run_pipeline.py
```

### 3. Run Streaming Pipeline (Optional)

**Start Kafka** (requires separate setup - see `docs/KAFKA_SETUP.md`):

```powershell
# Terminal 1: Start Zookeeper
cd C:\kafka
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# Terminal 2: Start Kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties

# Terminal 3: Producer
python src/streaming/kafka_producer.py

# Terminal 4: Consumer
python src/streaming/kafka_consumer.py
```

## 📊 Features

### Batch Processing
- Partitioned data lake storage
- Data quality validation (target ≥95%)
- 13 engineered features
- Collaborative filtering model
- Automated orchestration with Airflow

### Real-time Streaming (NEW! 🆕)
- Apache Kafka integration
- Real-time transaction ingestion
- Near real-time feature updates
- Event-driven architecture
- Scalable consumer groups

## 🏗️ Architecture

```
┌──────────────┐        ┌──────────────┐
│  Batch Data  │        │   Kafka      │
│  (CSV/JSON)  │        │   Stream     │
└──────┬───────┘        └──────┬───────┘
       │                       │
       │                       │
       ▼                       ▼
┌────────────────────────────────────┐
│        Data Lake (Partitioned)      │
│  raw/ | validated/ | prepared/     │
│          features/ | streaming/     │
└─────────────────┬──────────────────┘
                  │
                  ▼
           ┌─────────────┐
           │Feature Store│
           │  (SQLite)   │
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │ ML Model    │
           │   (SVD)     │
           └──────┬──────┘
                  │
                  ▼
          ┌──────────────┐
          │Recommendations│
          └──────────────┘
```

## 📁 Project Structure

```
ecommerce-data-engineering-ml/
├── data/                      # Raw data sources
├── storage/                   # Data lake (partitioned)
│   ├── raw/                  # Batch ingested data
│   ├── prepared/             # Cleaned data
│   ├── features/             # Engineered features
│   └── streaming/            # Real-time stream data
├── src/
│   ├── ingestion/            # Batch data ingestion
│   ├── streaming/            # Kafka producer/consumer
│   ├── validation/           # Quality checks
│   ├── preparation/          # Data cleaning
│   ├── features/             # Feature engineering & store
│   ├── models/               # ML models
│   └── utils/                # Common utilities
├── airflow/dags/             # Orchestration DAGs
├── models/                   # Saved models
├── docs/                     # Documentation
└── run_pipeline.py           # Master pipeline
```

## 📚 Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) - Complete installation and usage
- [Kafka Setup](docs/KAFKA_SETUP.md) - Real-time streaming configuration
- [Airflow Setup](docs/AIRFLOW_SETUP.md) - Orchestration setup
- [Feature Logic](docs/FEATURE_LOGIC.md) - Feature engineering details
- [DVC Workflow](docs/DVC_WORKFLOW.md) - Data versioning
- [Storage Structure](docs/STORAGE_STRUCTURE.md) - Data lake architecture
- [Project Summary](PROJECT_SUMMARY.md) - Complete overview

## 🎯 Success Criteria

- ✓ Precision@10 ≥ 0.15
- ✓ Recall@10 ≥ 0.10
- ✓ NDCG@10 ≥ 0.20
- ✓ Data Quality Score ≥ 95%
- ✓ Pipeline Latency < 24 hours (batch)
- ✓ Real-time processing < 1 second (streaming)

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| Data Processing | pandas, numpy |
| Streaming | Apache Kafka |
| Storage | Parquet, SQLite |
| Feature Store | Custom SQLite |
| ML | scikit-surprise (SVD) |
| Orchestration | Apache Airflow |
| Versioning | DVC |
| Logging | Custom logger |

## 🚦 Running Components

### Batch Pipeline
```powershell
python run_pipeline.py
```

### Individual Stages
```powershell
python src/ingestion/run_all_ingestion.py
python src/validation/validate_data.py
python src/preparation/clean_data.py
python src/features/engineer_features.py
python src/features/feature_store.py
python src/models/collaborative_filtering.py
```

### Streaming
```powershell
python src/streaming/kafka_producer.py
python src/streaming/kafka_consumer.py
```

### Airflow
```powershell
airflow webserver --port 8080  # Terminal 1
airflow scheduler              # Terminal 2
```

## 📊 Assignment Coverage

✅ All 10 tasks completed:
1. Problem Formulation
2. Data Ingestion (Batch + Streaming)
3. Raw Data Storage
4. Data Validation
5. Data Preparation
6. Feature Engineering
7. Feature Store
8. Data Versioning (DVC)
9. Model Training & Evaluation
10. Pipeline Orchestration

**Bonus**: Real-time streaming with Apache Kafka!

## 📝 License

Internal project for RecoMart

## 👥 Team

Data Platform Team - RecoMart
