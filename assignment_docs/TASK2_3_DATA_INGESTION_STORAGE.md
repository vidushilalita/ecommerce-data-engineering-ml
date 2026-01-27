# Task 2 & 3: Data Ingestion and Storage

## Overview

This document describes the data ingestion and storage architecture for the RecoMart E-commerce Recommendation System. The system supports both **batch ingestion** from files and **real-time streaming** via a FastAPI + Kafka architecture.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA INGESTION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     BATCH PIPELINE                                        │
│  │ Source Files │                                                           │
│  │ (CSV/JSON)   │                                                           │
│  └──────────────┘                                                           │
│        │              ┌─────────────┐              ┌──────────────┐         │
│        │              │  Ingestion  │              │  Data Lake   │         │
│        └─────────────►│   Modules   │─────────────►│   Storage    │         │
│                       └─────────────┘              │  (Parquet)   │         │
│                             ▲                      └──────────────┘         │
│                             │_____________________________                  │
│  ┌──────────────┐     STREAMING PIPELINE                  │                 │
│  │   External   │                                         │                 │
│  │   Clients    │                                         │                 │
│  └──────────────┘                                         │                 │
│        │              ┌─────────────┐              ┌──────────────┐         │
│        │              │   FastAPI   │              │    Kafka     │         │
│        └─────────────►│     API     │─────────────►│   Consumer   │         |
│                       └─────────────┘              └──────────────┘         │
│                             │                                               │
│                             ▼                                               │
│                       ┌─────────────┐                                       │
│                       │    Kafka    │                                       │
│                       │   Topics    │                                       │
│                       └─────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### 1. User Data
- **Source Files**: CSV files containing `user` in the filename
- **Location**: `data/` directory
- **Schema**:

| Column    | Type    | Description                          |
|-----------|---------|--------------------------------------|
| user_id   | Integer | Unique user identifier               |
| age       | Integer | User's age (must be > 0)             |
| gender    | String  | Gender (`M` or `F`)                  |
| device    | String  | Device type (`Mobile`, `Desktop`, `Tablet`) |

### 2. Product Data
- **Source File**: `products.json`
- **Location**: `data/` directory
- **Schema**:

| Column    | Type    | Description                          |
|-----------|---------|--------------------------------------|
| item_id   | Integer | Unique product identifier            |
| price     | Float   | Product price                        |
| brand     | String  | Product brand                        |
| category  | String  | Product category                     |
| rating    | Float   | Product rating                       |
| in_stock  | Boolean | Stock availability status            |

### 3. Transaction Data
- **Source Files**: CSV files containing `transaction` in the filename
- **Location**: `data/` directory
- **Schema**:

| Column     | Type     | Description                              |
|------------|----------|------------------------------------------|
| user_id    | Integer  | User who performed the action            |
| item_id    | Integer  | Product involved in the transaction      |
| view_mode  | String   | Interaction type (`view`, `add_to_cart`, `purchase`) |
| rating     | Integer  | Optional rating (1-5)                    |
| timestamp  | DateTime | When the interaction occurred            |

---

## Batch Ingestion Pipeline

### User Data Ingestion

**Module**: `src/ingestion/ingest_users.py`

**Class**: `UserDataIngestion`

#### Pipeline Steps:
1. **Discover Source Files**: Scan `data/` directory for user CSV files
2. **Validate Files**: Verify file existence and accessibility
3. **Read & Parse**: Load each CSV file into a pandas DataFrame
4. **Merge Datasets**: Combine all user DataFrames
5. **Clean Data**: Normalize types, handle nulls, strip whitespace
6. **Store**: Save to partitioned data lake storage as Parquet

### Product Data Ingestion

**Module**: `src/ingestion/ingest_products.py`

**Class**: `ProductDataIngestion`

#### Pipeline Steps:
1. **Validate Source File**: Confirm `products.json` exists
2. **Read JSON**: Parse product array from JSON file
3. **Convert to DataFrame**: Transform JSON to tabular format
4. **Validate Data**: Check for missing columns and null values
5. **Store**: Save to partitioned data lake as Parquet

---

### Transaction Data Ingestion

**Module**: `src/ingestion/ingest_transactions.py`

**Class**: `TransactionDataIngestion`

#### Pipeline Steps:
1. **Discover Files**: Scan for transaction CSV files
2. **Validate Sources**: Verify file accessibility
3. **Read & Merge**: Load and concatenate all transaction files
4. **Parse Timestamps**: Convert timestamp strings to datetime
5. **Validate Data**: Check view_mode values and column presence
6. **Store**: Save to partitioned storage

---

## Real-Time Streaming Pipeline

### Overview

The streaming pipeline enables real-time data ingestion through a FastAPI REST API backed by Apache Kafka message queues.

### Components

#### 1. FastAPI Application (`src/api/main.py`)

**Base URL**: `http://localhost:8000`

Provides REST endpoints for:
- Accepting user registrations and transaction events
- Publishing events to Kafka topics
- Internal endpoints for Kafka consumer to persist data

#### 2. Kafka Producer (`src/streaming/kafka_producer.py`)

**Class**: `TransactionProducer`

- Serializes events as JSON
- Publishes to configurable Kafka topics
- Implements retry logic with acknowledgment (`acks='all'`)

#### 3. Kafka Consumer (`src/streaming/kafka_consumer.py`)

**Class**: `TransactionConsumer`

- Subscribes to multiple topics (`recomart-users`, `recomart-transactions`)
- Forwards received events to internal API endpoints
- Supports consumer groups for scalability

### Data Flow

```
Client Request → FastAPI (Public Endpoint) → Kafka Producer → Kafka Topic
                                                                    │
                                                                    ▼
CSV Staging File ← FastAPI (Internal Endpoint) ← Kafka Consumer ◄──┘
```

### Kafka Topics

| Topic                    | Description                          |
|--------------------------|--------------------------------------|
| `recomart-users`         | User registration events             |
| `recomart-transactions`  | Transaction/interaction events       |

---

## Storage Layer

### Data Lake Structure

The storage layer uses a partitioned directory structure managed by `DataLakeStorage` class.

**Module**: `src/utils/storage.py`

### Directory Structure

```
storage/
├── raw/                          # Raw ingested data
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
│           ├── transactions_merged.parquet
│           └── transactions_merged_metadata.json
├── validated/                    # Validated data
├── prepared/                     # Cleaned & prepared data
└── features/                     # Feature store data
```

### Partitioning Strategy

- **Format**: `storage/{data_type}/{source}/{YYYY-MM-DD}/`
- **Time-based partitioning**: Data is organized by ingestion date
- **Supports**: Multiple data layers (raw, validated, prepared, features)

### Metadata Tracking

Each stored file includes a companion metadata JSON file containing:

| Field              | Description                                    |
|--------------------|------------------------------------------------|
| source             | Data source name (users, products, transactions) |
| data_type          | Data layer (raw, validated, prepared)          |
| timestamp          | ISO format ingestion timestamp                 |
| file_path          | Full path to the data file                     |
| file_size_bytes    | File size in bytes                             |
| record_count       | Number of records stored                       |
| schema.columns     | List of column names                           |
| schema.dtypes      | Column data types                              |
| checksum_md5       | MD5 hash for integrity verification            |
| null_counts        | Null count per column                          |
| memory_usage_bytes | DataFrame memory usage                         |

---

## API Documentation

### Public Endpoints

#### POST `/users`
Create a new user registration event.

**Request Body**:
```json
{
    "user_id": 1001,
    "age": 28,
    "gender": "M",
    "device": "Mobile"
}
```

**Response** (201 Created):
```json
{
    "status": "accepted",
    "user_id": 1001
}
```

**Validation Rules**:
- `user_id`: Required, integer
- `age`: Required, integer > 0
- `gender`: Required, one of `M`, `F`
- `device`: Required, one of `Mobile`, `Desktop`, `Tablet`

---

#### POST `/transactions`
Create a new transaction event.

**Request Body**:
```json
{
    "user_id": 1001,
    "item_id": 150,
    "view_mode": "purchase",
    "rating": 5,
    "timestamp": "2026-01-27T10:30:00"
}
```

**Response** (201 Created):
```json
{
    "status": "accepted",
    "user_id": 1001
}
```

**Validation Rules**:
- `user_id`: Required, integer
- `item_id`: Required, integer
- `view_mode`: Required, one of `view`, `add_to_cart`, `purchase`
- `rating`: Optional, integer 1-5
- `timestamp`: Optional, ISO datetime (defaults to current time)

---

#### GET `/health`
Health check endpoint.

**Response**:
```json
{
    "status": "healthy"
}
```

---

### Internal Endpoints (Kafka Consumer Use Only)

#### POST `/internal/ingest-user`
Called by Kafka Consumer to persist user data to CSV staging file.

#### POST `/internal/ingest-transaction`
Called by Kafka Consumer to persist transaction data to CSV staging file.

---

## Configuration

### Configuration File: `src/config.json`

```json
{
    "data_dir": "data",
    "storage_base": "storage",
    "products_file": "products.json",
    "interactions_file": "interactions.json",
    "users_file": "users.json"
}
```

### Configuration Parameters

| Parameter         | Description                              | Default     |
|-------------------|------------------------------------------|-------------|
| data_dir          | Directory containing source data files   | `data`      |
| storage_base      | Base directory for data lake storage     | `storage`   |
| products_file     | Name of the products JSON file           | `products.json` |

### Kafka Configuration

| Parameter           | Default Value      | Description                      |
|---------------------|--------------------|----------------------------------|
| bootstrap_servers   | `localhost:9092`   | Kafka broker address             |
| group_id            | `recomart-consumer-group` | Consumer group identifier |
| acks                | `all`              | Producer acknowledgment setting  |
| retries             | `3`                | Number of retry attempts         |

---

## Running the Pipelines

### Prerequisites

1. **Python Environment**: Python 3.8+
2. **Dependencies**: Install via `pip install -r requirements.txt`
3. **Kafka** (for streaming): Running Kafka broker on `localhost:9092`


### Real-Time Streaming

#### 1. Start the FastAPI Server:
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Start Kafka Consumer:
```bash
python -m src.streaming.kafka_consumer
```

#### 3. Send Test Events:
```bash
# Create a user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1001, "age": 25, "gender": "F", "device": "Mobile"}'

# Create a transaction
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1001, "item_id": 150, "view_mode": "purchase", "rating": 5}'
```

### Staging Files

Real-time streaming data is staged in:
- **Users**: `data/users_api_staging.csv`
- **Transactions**: `data/transactions_api_staging.csv`

---

## Error Handling

### Batch Pipeline Errors

| Error Type           | Handling                                      |
|----------------------|-----------------------------------------------|
| FileNotFoundError    | Logged and raised with descriptive message    |
| EmptyDataError       | Logged, empty DataFrame returned              |
| ParseError           | Logged with details, exception propagated     |
| ValidationWarning    | Logged as warning, processing continues       |

### Streaming Pipeline Errors

| Error Type           | Handling                                      |
|----------------------|-----------------------------------------------|
| Kafka Connection     | Retry with backoff, log failure               |
| API Timeout          | 5-second timeout, error logged                |
| Serialization Error  | JSON encoding with default string conversion  |

---

## Logging
**Log Output**: Console and `logs/` directory (when configured)

---
