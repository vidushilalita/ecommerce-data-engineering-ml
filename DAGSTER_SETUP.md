# RecoMart Dagster Orchestration Guide

## Overview

This guide provides complete instructions for orchestrating the RecoMart data pipeline using **Dagster**, a lightweight, modern data orchestration framework.

---

## Quick Start (2 minutes)

### Windows Users

```bash
# 1. Install dependencies
run_pipeline.bat install

# 2. Start Web UI
run_pipeline.bat ui

# 3. Open http://localhost:3000 in browser
# 4. Click on "complete_pipeline_job"
# 5. Click "Materialize" button to run
```

### Linux/macOS Users

```bash
# 1. Make script executable
chmod +x run_pipeline.sh

# 2. Install dependencies
./run_pipeline.sh install

# 3. Start Web UI
./run_pipeline.sh ui

# 4. Open http://localhost:3000 in browser
# 5. Click on "complete_pipeline_job"
# 6. Click "Materialize" button to run
```

### Any Platform (Python)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Web UI
python run_dagster_pipeline.py --ui

# 3. Open http://localhost:3000 in browser
```

---

## What is Dagster?

**Dagster** is a lightweight data orchestration framework that:

- ✅ **Visual Pipeline DAGs** - See your pipeline as a beautiful directed graph
- ✅ **Type-Safe** - Define inputs/outputs with Python type hints
- ✅ **Web UI** - Monitor, debug, and manage runs from browser
- ✅ **Lightweight** - Uses SQLite (no external database needed)
- ✅ **Observable** - Built-in data quality metrics and lineage
- ✅ **Python Native** - Pure Python, easy to test and integrate
- ✅ **Production Ready** - Scales from laptop to enterprise

**Compare to alternatives**:
- vs Airflow: Simpler, more Python-native, lighter
- vs Prefect: Similar, but Dagster has better data observability
- vs manual scripting: Adds monitoring, error handling, parallelization

---

## Pipeline Architecture

```
COMPLETE PIPELINE (complete_pipeline_job)
═══════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────┐
    │  INGESTION (Parallel)                                   │
    │  ├─ ingest_users_op        (load users CSV)             │
    │  ├─ ingest_products_op     (load products JSON)         │
    │  └─ ingest_transactions_op (load transactions CSV)      │
    └─────────────────────────────────────────────────────────┘
                          │
                          ↓
    ┌─────────────────────────────────────────────────────────┐
    │  VALIDATION                                             │
    │  └─ validate_data_op       (check data quality)         │
    └─────────────────────────────────────────────────────────┘
                          │
                          ↓
    ┌─────────────────────────────────────────────────────────┐
    │  PREPARATION                                            │
    │  └─ prepare_data_op        (clean, encode, normalize)   │
    └─────────────────────────────────────────────────────────┘
                          │
                          ↓
    ┌─────────────────────────────────────────────────────────┐
    │  FEATURE ENGINEERING                                    │
    │  └─ engineer_features_op   (create ML features)         │
    └─────────────────────────────────────────────────────────┘
                          │
                          ↓
    ┌─────────────────────────────────────────────────────────┐
    │  MODEL TRAINING                                         │
    │  └─ train_model_op         (SVD collaborative filtering)│
    └─────────────────────────────────────────────────────────┘
                          │
                          ↓
                    [Trained Model]
                models/collaborative_filtering.pkl
```

---

## Running the Pipeline

### Method 1: Web UI (Recommended) ⭐

**Best for**: Visual monitoring, debugging, learning

```bash
dagster dev
```

Then:
1. Open http://localhost:3000
2. Click on job name (e.g., `complete_pipeline_job`)
3. Review the DAG visualization
4. Click "Materialize" button to execute
5. Watch ops execute in real-time
6. Click on ops to see logs and outputs

**Web UI Features**:
- Real-time execution status
- Op-level logging
- Data lineage visualization
- Execution history
- Performance metrics

---

### Method 2: Command Line

**Best for**: Automation, CI/CD, scripts

```bash
# Run complete pipeline
dagster job execute -f src/orchestration/dagster_pipeline.py -j complete_pipeline_job

# Run ingestion only
dagster job execute -f src/orchestration/dagster_pipeline.py -j ingestion_job

# With custom config
dagster job execute -f src/orchestration/dagster_pipeline.py \
  -j complete_pipeline_job \
  -c config.yaml
```

---

### Method 3: Python Script

**Best for**: Programmatic execution, integration

```bash
# Run with default settings (complete pipeline)
python run_dagster_pipeline.py

# Run ingestion only
python run_dagster_pipeline.py --ingestion-only

# Start web UI
python run_dagster_pipeline.py --ui
```

---

### Method 4: Interactive Menu

**Best for**: Users who want guided options

```bash
# Windows
run_pipeline.bat

# Linux/macOS
./run_pipeline.sh

# Python (any platform)
python dagster_quickstart.py
```

Select from menu and follow prompts.

---

## Available Jobs

### Job 1: `ingestion_job`

**Purpose**: Data ingestion only (no downstream processing)

**Runs these ops in parallel**:
- `ingest_users_op` - Load users from CSV files
- `ingest_products_op` - Load products from JSON
- `ingest_transactions_op` - Load transactions from CSV

**Execution time**: 2-3 seconds

**Output**: Raw data in `storage/raw/`

**Use when**:
- You just need fresh source data
- Testing ingestion in isolation
- Debugging data source issues

**Example**:
```bash
dagster job execute -f src/orchestration/dagster_pipeline.py -j ingestion_job
```

---

### Job 2: `complete_pipeline_job`

**Purpose**: Full end-to-end pipeline (everything)

**Runs these ops in sequence**:
1. **Ingestion** (parallel)
   - `ingest_users_op` - Load users
   - `ingest_products_op` - Load products
   - `ingest_transactions_op` - Load transactions

2. **Validation**
   - `validate_data_op` - Comprehensive data quality checks

3. **Preparation**
   - `prepare_data_op` - Clean, encode, normalize data

4. **Feature Engineering**
   - `engineer_features_op` - Create user, item, interaction features

5. **Model Training**
   - `train_model_op` - Train SVD collaborative filtering model

**Execution time**: 10-15 seconds

**Output**:
- Cleaned data: `storage/prepared/`
- Features: `storage/features/`
- Trained model: `models/collaborative_filtering.pkl`

**Use when**:
- You want to run the entire pipeline
- Production deployments
- Getting fresh model artifacts

**Example**:
```bash
dagster job execute -f src/orchestration/dagster_pipeline.py -j complete_pipeline_job
```

---

## Understanding the Web UI

### Dashboard Overview

```
┌─────────────────────────────────────────────────────────┐
│  DAGSTER WEB UI (http://localhost:3000)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  LEFT SIDEBAR:                                          │
│  ├─ Repository                                          │
│  │  └─ Complete Pipeline Job                            │
│  │  └─ Ingestion Job                                    │
│  └─ Runs (execution history)                            │
│                                                          │
│  MAIN AREA:                                             │
│  ├─ Job Definition (DAG visualization)                  │
│  ├─ Materialize button (run job)                        │
│  └─ Configuration panel                                 │
│                                                          │
│  DURING EXECUTION:                                      │
│  ├─ Op status (pending/running/success/failure)         │
│  ├─ Real-time logs                                      │
│  └─ Duration tracking                                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Key UI Elements

**1. Repository Panel** (Left Sidebar)
- Lists all available jobs
- Click to view job definition

**2. Job Graph** (Main Area)
- Visual DAG of ops and dependencies
- Color-coded by status
- Click ops for details

**3. Logs** (Bottom Tab)
- Real-time log streaming
- Op-level logging
- Timestamp per message

**4. Runs** (History)
- Past executions
- Status, duration, timestamp
- Click to view details

**5. Data Observability** (Advanced)
- Record counts per op
- Data quality metrics
- Output schemas

---

## Execution Flow Example

**Running `complete_pipeline_job`**:

```
Time    Event
────────────────────────────────────────────────────────────

0:00s   Starting pipeline execution
        Status: STARTED

0:05s   ✓ ingest_users_op succeeded
        Records: 1383

0:10s   ✓ ingest_products_op succeeded
        Records: 101

0:15s   ✓ ingest_transactions_op succeeded
        Records: 3001

0:20s   ✓ validate_data_op succeeded
        Quality Score: 95%

0:25s   ✓ prepare_data_op succeeded
        Users: 1383, Products: 101, Transactions: 3001

0:30s   ✓ engineer_features_op succeeded
        User features: 1383, Item features: 101, Interactions: 3001

0:40s   ✓ train_model_op succeeded
        Model saved to: models/collaborative_filtering.pkl

0:40s   Pipeline completed successfully!
```

---

## Monitoring & Logs

### View Logs

**In Web UI**:
1. Open http://localhost:3000
2. Start a run (click "Materialize")
3. Click on an op in the DAG
4. Switch to "Logs" tab
5. See real-time logging output

**Sample Log Output**:
```
2026-01-27 10:30:45 INFO  Starting user data ingestion...
2026-01-27 10:30:46 INFO  Discovered 2 user data files
2026-01-27 10:30:47 INFO  Read 927 records from users1.csv
2026-01-27 10:30:48 INFO  Read 456 records from users2.csv
2026-01-27 10:30:49 INFO  Merged dataset contains 1383 records
2026-01-27 10:30:50 INFO  Stored at: storage/raw/users/2026-01-27/users_merged.parquet
```

### Performance Metrics

Each op tracks:
- **Duration**: How long it took
- **Records**: Number of records processed
- **File size**: Output data size
- **Schema**: Column names and types
- **Checksum**: Data integrity hash

---

## Configuration

### Dagster Configuration File

Located at `dagster.yaml`:

```yaml
instance:
  run_storage:
    module: dagster.core.storage.runs
    class: SqliteRunStorage
    config:
      base_dir: ./dagster_data

  event_log_storage:
    module: dagster.core.storage.event_log
    class: SqliteEventLogStorage
    config:
      base_dir: ./dagster_data

  compute_logs:
    module: dagster.core.storage.compute_logs
    class: LocalComputeLogManager
    config:
      base_dir: ./dagster_data/logs

execution:
  config:
    multiprocess:
      max_concurrent: 4
```

**Key settings**:

| Setting | Purpose |
|---------|---------|
| `run_storage` | Stores execution history |
| `event_log_storage` | Stores event logs |
| `compute_logs` | Stores op output logs |
| `max_concurrent` | Max parallel ops |

### Custom Op Configuration

Pass configuration to ops at runtime:

```yaml
# config.yaml
ops:
  ingest_users_op:
    config:
      data_dir: "data"
      storage_base: "storage"
```

Run with config:
```bash
dagster job execute -f ... -c config.yaml
```

---

## Troubleshooting

### Problem: "Dagster command not found"

```bash
# Solution 1: Install Dagster
pip install dagster dagster-webui

# Solution 2: Verify installation
python -m dagster --version

# Solution 3: On Windows, restart terminal after install
```

---

### Problem: "Port 3000 already in use"

```bash
# Use different port
dagster dev --port 3001

# Or kill the process using port 3000
# Windows (PowerShell):
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force

# Linux/macOS:
lsof -ti:3000 | xargs kill -9
```

---

### Problem: "Repository not found"

```bash
# Make sure you're in project root
cd c:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml

# Set Python path
set PYTHONPATH=.  # Windows
export PYTHONPATH=. # Linux/macOS

# Try again
dagster dev
```

---

### Problem: "Module not found errors"

```bash
# Solution 1: Install dependencies again
pip install -r requirements.txt --upgrade

# Solution 2: Install project in development mode
pip install -e .

# Solution 3: Manually add path in Python
import sys
sys.path.insert(0, '/path/to/project')
```

---

### Problem: "dagster_data directory permission denied"

```bash
# Linux/macOS: Set permissions
chmod 755 dagster_data

# Windows: Use folder properties → Security to set write permissions
# Or run terminal as Administrator
```

---

## File Structure

```
ecommerce-data-engineering-ml/
├── src/
│   └── orchestration/
│       ├── dagster_pipeline.py         ← Op and job definitions
│       ├── repository.py               ← Repository configuration
│       └── __init__.py
│
├── docs/
│   ├── DAGSTER_ORCHESTRATION.md       ← Detailed documentation
│   └── DAGSTER_QUICKSTART.md          ← Quick reference
│
├── dagster.yaml                        ← Dagster configuration
├── run_dagster_pipeline.py             ← Python execution script
├── dagster_quickstart.py               ← Interactive menu (Python)
├── run_pipeline.bat                    ← Windows batch script
├── run_pipeline.sh                     ← Linux/macOS shell script
└── requirements.txt                    ← Python dependencies
```

---

## Advanced Features

### Scheduled Runs (Production)

Add to `src/orchestration/repository.py`:

```python
from dagster import schedule

@schedule(
    job=complete_pipeline_job,
    cron_schedule="0 2 * * *",  # 2 AM daily
)
def daily_pipeline(context):
    return {}
```

### Data Sensors

Trigger pipeline when files change:

```python
from dagster import sensor

@sensor(job=ingestion_job)
def data_files_sensor(context):
    if new_files_in_data_dir():
        yield RunRequest()
```

### Custom Ops

Define your own operations:

```python
@op(config_schema={"param": str})
def my_op(context) -> Dict:
    context.log.info(f"Running with param: {context.op_config['param']}")
    return {"status": "success"}
```

---

## Deployment Options

### Local Development
```bash
dagster dev
```

### CI/CD Pipeline
```yaml
# GitHub Actions
- name: Run Pipeline
  run: pip install -r requirements.txt && dagster job execute ...
```

### Docker Container
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["dagster", "dev"]
```

---

## Performance Optimization

### Parallelization

Ingestion ops run in parallel (automatic):
```
Time with parallelization: 2-3s
Time without:             6-9s

Speedup: 3x faster
```

### Adjust Concurrency

Edit `dagster.yaml`:
```yaml
execution:
  config:
    multiprocess:
      max_concurrent: 8  # increase for more parallel ops
```

### Resource Limits

```bash
# Monitor memory and CPU
dagster dev --debug  # Verbose logging
```

---

## Resources

- **Quick Reference**: `docs/DAGSTER_QUICKSTART.md`
- **Detailed Guide**: `docs/DAGSTER_ORCHESTRATION.md`
- **Code**: `src/orchestration/dagster_pipeline.py`
- **Official Docs**: https://docs.dagster.io/
- **Slack Community**: https://dagster.io/community

---

## Summary

**Dagster provides**:
- ✅ Visual pipeline orchestration
- ✅ Easy-to-use web UI
- ✅ Built-in data observability
- ✅ Lightweight & no external database
- ✅ Type-safe op definitions
- ✅ Production-ready features

**Get started**:
1. Run `run_pipeline.bat install` (Windows) or `./run_pipeline.sh install` (Linux/macOS)
2. Run `run_pipeline.bat ui` or `./run_pipeline.sh ui`
3. Open http://localhost:3000
4. Click "Materialize" on a job

**Questions?** Check the detailed documentation or Dagster's official docs.

Happy orchestrating! 🚀
