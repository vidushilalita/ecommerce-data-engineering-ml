# Dagster Pipeline Orchestration - Setup & Usage Guide

## Overview

This guide provides complete instructions for setting up and running the **Dagster-based orchestration pipeline** for the RecoMart data engineering and ML training workflow.

**Dagster** is a lightweight, modern orchestration engine perfect for:
- Data pipeline visualization and monitoring
- Dependency management between tasks
- Built-in data observability
- Easy-to-use web UI for monitoring
- No external database required for lightweight projects

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Project Structure](#project-structure)
5. [Available Pipelines](#available-pipelines)
6. [Running Pipelines](#running-pipelines)
7. [Web UI Overview](#web-ui-overview)
8. [Monitoring & Observability](#monitoring--observability)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Usage](#advanced-usage)

---

## Prerequisites

### Requirements

- **Python 3.8+**
- **Operating System**: Windows, macOS, or Linux
- **Package Manager**: pip (already included with Python)

### Dependencies

All required packages are listed in `requirements.txt`. Key orchestration packages:

```
dagster>=1.5.0
dagster-postgres>=0.19.0  # Optional: for production database storage
pandas>=1.3.0
scikit-learn>=1.0.0
surprise>=0.1
```

---

## Installation

### Step 1: Install Dagster

```bash
# Navigate to project root
cd c:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml

# Install Dagster and dependencies
pip install dagster dagster-webui

# Or install all project dependencies at once
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
# Check Dagster version
dagster --version

# Should output: dagster, version X.X.X
```

### Step 3: Create Required Directories

```bash
# Dagster will create these automatically, but you can pre-create them
mkdir dagster_data
mkdir logs
mkdir models
```

---

## Configuration

### Dagster Configuration File

The `dagster.yaml` file in the project root configures:

**Key Settings**:

| Setting | Purpose | Default |
|---------|---------|---------|
| `run_storage` | Stores run history and metadata | SQLite at `./dagster_data` |
| `event_log_storage` | Stores event logs | SQLite at `./dagster_data` |
| `compute_logs` | Stores execution logs | Local directory `./dagster_data/logs` |
| `max_concurrent` | Maximum parallel ops | 4 |

### Environment Setup (Optional)

Create a `.env` file in the project root for custom settings:

```bash
# .env file (create if needed)
DAGSTER_HOME=./dagster_data
PYTHONPATH=.
```

---

## Project Structure

```
ecommerce-data-engineering-ml/
├── src/
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── dagster_pipeline.py       # ← Pipeline definitions (ops & jobs)
│   │   ├── repository.py              # ← Repository configuration
│   │   └── __pycache__/
│   ├── ingestion/
│   │   ├── ingest_users.py
│   │   ├── ingest_products.py
│   │   └── ingest_transactions.py
│   ├── validation/
│   │   └── validate_data.py
│   ├── preparation/
│   │   └── clean_data.py
│   ├── features/
│   │   └── engineer_features.py
│   ├── model_training/
│   │   └── collaborative_filtering.py
│   └── utils/
│       ├── storage.py
│       └── logger.py
├── data/                              # Source data directory
├── storage/                           # Data lake (created during runs)
├── models/                            # Trained models
├── dagster_data/                      # Dagster metadata (auto-created)
├── dagster.yaml                       # ← Dagster configuration
└── requirements.txt
```

---

## Available Pipelines

### 1. Ingestion Pipeline (`ingestion_job`)

**Purpose**: Run data ingestion only

**Operations** (run in parallel):
- `ingest_users_op` - Load user CSV files
- `ingest_products_op` - Load product JSON
- `ingest_transactions_op` - Load transaction CSVs

**Output**: Raw data stored in `storage/raw/` as Parquet files

**Use Case**: 
- Refresh data from source files
- Test ingestion without running full pipeline
- Debug data source issues

---

### 2. Complete Pipeline (`complete_pipeline_job`)

**Purpose**: Run entire end-to-end pipeline

**Operations** (in sequence):
1. **Ingestion** (parallel):
   - `ingest_users_op`
   - `ingest_products_op`
   - `ingest_transactions_op`

2. **Validation**:
   - `validate_data_op` - Check data quality (depends on ingestion)

3. **Preparation**:
   - `prepare_data_op` - Clean and normalize data (depends on validation)

4. **Feature Engineering**:
   - `engineer_features_op` - Create ML features (depends on preparation)

5. **Model Training**:
   - `train_model_op` - Train collaborative filtering model (depends on features)

**Output**: 
- Cleaned data in `storage/prepared/`
- Features in `storage/features/`
- Trained model in `models/collaborative_filtering.pkl`

**Use Case**: Full end-to-end pipeline execution

---

## Running Pipelines

### Method 1: Dagster Web UI (Recommended)

The web UI provides visualization, monitoring, and execution capabilities.

#### Start the Web UI

```bash
# From project root directory
cd c:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml

# Start Dagster development server
dagster dev
```

**Output**:
```
Launching Dagster UI...
Serving Dagster UI on http://localhost:3000
```

**Access the UI**:
1. Open web browser
2. Navigate to `http://localhost:3000`
3. See the repository loaded with available jobs

#### Execute Job from Web UI

1. Click on a job (e.g., `complete_pipeline_job`)
2. Review the job graph
3. Click "**Materialize**" button to execute
4. Monitor execution in real-time with:
   - Op status (running, success, failure)
   - Execution logs
   - Duration and performance metrics
   - Data observability (record counts, outputs)

---

### Method 2: Command Line (CLI)

Execute jobs without the web UI using CLI commands.

#### Run Ingestion Job

```bash
# Run ingestion pipeline
dagster job execute -f src/orchestration/dagster_pipeline.py -j ingestion_job

# With custom workspace
dagster job execute -f src/orchestration/repository.py -j ingestion_job
```

#### Run Complete Pipeline

```bash
# Run full pipeline
dagster job execute -f src/orchestration/dagster_pipeline.py -j complete_pipeline_job
```

#### With Config Override (Advanced)

```bash
# Run with custom configuration
dagster job execute \
  -f src/orchestration/dagster_pipeline.py \
  -j complete_pipeline_job \
  --config config_override.yaml
```

---

### Method 3: Python Script

Execute jobs programmatically from Python.

#### Direct Execution

```python
# run_dagster_pipeline.py
from src.orchestration.dagster_pipeline import complete_pipeline_job
from dagster import execute_job

# Execute the job
result = execute_job(complete_pipeline_job)

# Check result
if result.success:
    print("Pipeline executed successfully!")
else:
    print("Pipeline failed!")
    print(result.all_events)
```

Run the script:
```bash
python run_dagster_pipeline.py
```

---

## Web UI Overview

### Dashboard Elements

**1. Repository View**
- Lists all available jobs
- Shows job definitions and DAG

**2. Job Graph**
- Visual representation of ops and dependencies
- Color-coded status (pending, running, success, failure)
- Click on ops to view details

**3. Execution History**
- Past runs with timestamps
- Duration and status
- Filter by job, status, or date range

**4. Run Details**
- Complete execution log for each run
- Op-level logging output
- Performance metrics (duration per op)
- Input/output data

**5. Data Observability**
- Record counts from ops
- Data quality metrics
- Output schema information

---

## Monitoring & Observability

### Logging

All ops produce detailed logs accessible via:

1. **Web UI**: 
   - Click on op → View logs tab
   - Real-time log streaming during execution

2. **Console Output**:
   - Logs printed to terminal when running CLI/Python

3. **Log Files**:
   - Location: `dagster_data/logs/`
   - Can be used for debugging and audit trails

### Example Log Output

```
2026-01-27 10:30:45 - INFO - ingest_users_op - Starting user data ingestion...
2026-01-27 10:30:46 - INFO - ingest_users_op - Discovered 2 user data files
2026-01-27 10:30:47 - INFO - ingest_users_op - Read 927 records from users1.csv
2026-01-27 10:30:48 - INFO - ingest_users_op - Read 456 records from users2.csv
2026-01-27 10:30:49 - INFO - ingest_users_op - Merged dataset contains 1383 total records
2026-01-27 10:30:50 - INFO - ingest_users_op - User ingestion complete: 1383 records
```

### Performance Metrics

**Duration Tracking**:
- Each op execution records duration
- Visible in execution history
- Helps identify bottlenecks

**Data Quality Metrics**:
- Record counts at each stage
- Null counts and validation issues
- Quality scores from validation ops

---

## Troubleshooting

### Issue 1: "Dagster command not found"

**Solution**: Dagster is not installed or not in PATH.

```bash
# Reinstall Dagster
pip install --upgrade dagster dagster-webui

# Verify installation
dagster --version
```

---

### Issue 2: "Repository not found"

**Solution**: Dagster can't locate the repository.

```bash
# Make sure you're in the project root
cd c:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml

# Start with explicit path
dagster dev -w src/orchestration/repository.py
```

---

### Issue 3: Ops failing with import errors

**Solution**: Python path is not set correctly.

```bash
# Option 1: Set PYTHONPATH environment variable
set PYTHONPATH=.

# Option 2: Install project in development mode
pip install -e .

# Option 3: Run from project root with proper path setup
cd /project/root && dagster dev
```

---

### Issue 4: Storage directory permissions

**Solution**: Dagster can't write to `dagster_data/`

```bash
# Create directory with proper permissions
mkdir dagster_data
chmod 755 dagster_data  # On Linux/macOS

# On Windows, ensure write permissions in folder properties
```

---

### Issue 5: Port 3000 already in use

**Solution**: Another service is using port 3000.

```bash
# Use alternative port
dagster dev --port 3001

# Or kill process using port 3000 (Windows PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
```

---

## Advanced Usage

### Custom Op Configuration

Modify op behavior via configuration:

```python
# In dagster_pipeline.py - Add @op config
@op(config_schema={
    "data_dir": Field(String, default_value="data"),
    "storage_base": Field(String, default_value="storage")
})
def ingest_users_op(context) -> Dict[str, Any]:
    data_dir = context.op_config["data_dir"]
    storage_base = context.op_config["storage_base"]
    # ... rest of op
```

Execute with custom config:

```bash
dagster job execute -f ... -c config.yaml
```

---

### Adding Schedules (Production Enhancement)

```python
# In repository.py
from dagster import schedule, ScheduleDefinition, DefaultSensorStatus

@schedule(
    job=complete_pipeline_job,
    cron_schedule="0 2 * * *",  # 2 AM daily
)
def daily_pipeline_schedule(context):
    return {}

# Add to repository
return [
    ingestion_job,
    complete_pipeline_job,
    daily_pipeline_schedule
]
```

---

### Adding Data Sensors (Advanced)

Monitor for changes and trigger automatically:

```python
# In dagster_pipeline.py
from dagster import sensor, trigger_sensor

@sensor(job=ingestion_job)
def data_file_sensor(context):
    """Trigger ingestion when new files appear"""
    data_dir = Path("data")
    files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.json"))
    
    if files:
        return SkipReason("Data files found, triggering ingestion")
```

---

### Integration with CI/CD

#### GitHub Actions Example

```yaml
# .github/workflows/pipeline.yml
name: Run Dagster Pipeline

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run Dagster pipeline
        run: |
          dagster job execute \
            -f src/orchestration/dagster_pipeline.py \
            -j complete_pipeline_job
```

---

## Performance Optimization

### 1. Parallel Execution

The pipeline uses parallel ingestion ops for maximum efficiency:

```
Execution Timeline (with parallelization):
0s:  [ingest_users_op] [ingest_products_op] [ingest_transactions_op]
     ↓
3s:  [validate_data_op] (waits for all ingestion)
     ↓
5s:  [prepare_data_op]
     ↓
7s:  [engineer_features_op]
     ↓
10s: [train_model_op]

Total: ~10 seconds (vs ~15 seconds without parallelization)
```

### 2. Multiprocessing

Configure Dagster for concurrent ops:

```yaml
# In dagster.yaml
execution:
  config:
    multiprocess:
      max_concurrent: 4
```

### 3. Resource Limits

Adjust based on system capacity:

```bash
# Run with memory limit
dagster dev --memory-limit 4GB
```

---

## Summary

**Quick Start**:
```bash
# 1. Install
pip install -r requirements.txt

# 2. Start UI
dagster dev

# 3. Navigate to http://localhost:3000
# 4. Click on 'complete_pipeline_job'
# 5. Click 'Materialize' to run
```

**Key Benefits**:
✅ Visual pipeline monitoring
✅ Parallel op execution
✅ Built-in data observability
✅ Lightweight (no external DB required)
✅ Easy deployment and scaling

**Next Steps**:
- Explore the web UI features
- Set up daily schedules for production
- Integrate with CI/CD pipeline
- Add custom sensors for data freshness monitoring
