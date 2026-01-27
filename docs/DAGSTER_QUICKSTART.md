# Dagster Orchestration - Complete Guide

## Quick Start (5 minutes)

### Step 1: Install Dagster
```bash
pip install -r requirements.txt
```

### Step 2: Start Web UI
```bash
dagster dev
```

### Step 3: Open Browser
Navigate to `http://localhost:3000` and click "Materialize" on any job.

---

## Overview

This project uses **Dagster** for orchestrating the complete RecoMart data pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│                   DAGSTER PIPELINE ARCHITECTURE             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Ingestion Layer (Parallel)                                │
│  ├─ ingest_users_op ────┐                                  │
│  ├─ ingest_products_op  ├─→ validate_data_op               │
│  └─ ingest_transactions_op                                 │
│                             │                               │
│                             ↓                               │
│                      prepare_data_op                        │
│                             │                               │
│                             ↓                               │
│                   engineer_features_op                      │
│                             │                               │
│                             ↓                               │
│                     train_model_op                          │
│                             │                               │
│                             ↓                               │
│                    [trained model]                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Why Dagster?

| Feature | Benefit |
|---------|---------|
| **Visual DAG** | See your pipeline in a beautiful graph |
| **Lightweight** | No external database required (SQLite-based) |
| **Type Safety** | Typed ops with input/output validation |
| **Web UI** | Monitor runs, logs, and metrics |
| **Data Observability** | Built-in schema and record count tracking |
| **Easy to Test** | Unit test individual ops |
| **Python Native** | Pure Python, easy to integrate |

---

## Running the Pipeline

### Option 1: Web UI (Recommended) ⭐

```bash
dagster dev
```

Then:
1. Open http://localhost:3000
2. Select a job (e.g., `complete_pipeline_job`)
3. Click "Materialize" button
4. Monitor execution in real-time

**Advantages**:
- Visual feedback
- Real-time logs
- Easy to debug
- Beautiful UI

---

### Option 2: Command Line

```bash
# Run complete pipeline
dagster job execute -f src/orchestration/dagster_pipeline.py -j complete_pipeline_job

# Run ingestion only
dagster job execute -f src/orchestration/dagster_pipeline.py -j ingestion_job
```

---

### Option 3: Python Script

```bash
# Run with defaults (complete pipeline)
python run_dagster_pipeline.py

# Run ingestion only
python run_dagster_pipeline.py --ingestion-only

# Start web UI
python run_dagster_pipeline.py --ui
```

---

### Option 4: Interactive Menu

```bash
# Launch interactive menu
python dagster_quickstart.py
```

Select from menu:
1. Check Dependencies
2. Install Dependencies
3. Start Web UI
4. Run Ingestion Only
5. Run Complete Pipeline
6. Exit

---

## Available Jobs

### 1. `ingestion_job`
**Runs**: Data ingestion only (parallel execution)

**Operations**:
- `ingest_users_op` - Load users from CSV
- `ingest_products_op` - Load products from JSON
- `ingest_transactions_op` - Load transactions from CSV

**Output**: Raw data in `storage/raw/`

**Use When**: You just need fresh data without processing

---

### 2. `complete_pipeline_job`
**Runs**: Full end-to-end pipeline

**Operations** (in sequence):
1. Parallel ingestion (users, products, transactions)
2. Data validation
3. Data preparation (cleaning, encoding, normalization)
4. Feature engineering (user, item, interaction features)
5. Model training (collaborative filtering with SVD)

**Output**: 
- Cleaned data: `storage/prepared/`
- Features: `storage/features/`
- Model: `models/collaborative_filtering.pkl`

**Use When**: You need to run the entire pipeline

---

## Project Structure

```
src/orchestration/
├── dagster_pipeline.py      ← Pipeline definitions (ops & jobs)
├── repository.py            ← Repository configuration
└── __init__.py

docs/
└── DAGSTER_ORCHESTRATION.md ← Detailed documentation

dagster.yaml                  ← Dagster configuration
run_dagster_pipeline.py       ← Python execution script
dagster_quickstart.py         ← Interactive menu script
```

---

## Key Concepts

### Ops (Operations)

An **op** is a unit of work:

```python
@op
def ingest_users_op(context) -> Dict[str, Any]:
    """Load user data from CSV files"""
    # Implementation
    return metadata
```

Features:
- Type hints for inputs/outputs
- Access to logging via `context.log`
- Can depend on other ops

### Jobs

A **job** is a collection of ops with dependencies:

```python
@job
def complete_pipeline_job():
    """Full pipeline"""
    return recomart_pipeline_graph()
```

### Graphs

A **graph** defines op dependencies:

```python
@graph
def recomart_pipeline_graph():
    users = ingest_users_op()
    products = ingest_products_op()
    validate = validate_data_op(users, products)
    return validate
```

---

## Monitoring Pipelines

### Web UI Dashboard

**Available at**: http://localhost:3000

**Features**:
- **Runs**: View execution history with status
- **Assets**: See data outputs and lineage
- **Logs**: Real-time log streaming per op
- **Instance**: System health and performance

### Real-time Monitoring

While running:
- See op status (running, success, failure)
- View logs in real-time
- Track duration per op
- See data outputs

### After Execution

- View complete execution log
- See performance metrics
- Check data quality stats
- Access all op outputs

---

## Troubleshooting

### "Dagster not found"

```bash
# Install Dagster
pip install dagster dagster-webui
```

### "Port 3000 already in use"

```bash
# Use different port
dagster dev --port 3001
```

### Import errors

```bash
# Ensure you're in project root
cd c:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml

# Set Python path
set PYTHONPATH=.

# Try again
dagster dev
```

### Storage permissions

```bash
# Create directory if missing
mkdir dagster_data

# On Windows, ensure write permissions
# Right-click folder → Properties → Security
```

---

## Configuration

Edit `dagster.yaml` to customize:

| Setting | Purpose |
|---------|---------|
| `run_storage` | Where run history is stored |
| `event_log_storage` | Where event logs are stored |
| `compute_logs` | Where execution logs are saved |
| `max_concurrent` | Max parallel ops |

---

## Advanced Features

### Custom Op Configuration

```python
@op(config_schema={"data_dir": str})
def my_op(context):
    data_dir = context.op_config["data_dir"]
```

Run with config:
```bash
dagster job execute ... --config config.yaml
```

### Scheduled Runs (Production)

```python
@schedule(job=complete_pipeline_job, cron_schedule="0 2 * * *")
def daily_pipeline(context):
    return {}
```

Runs automatically at 2 AM daily.

### Data Sensors

Trigger pipeline when files change:

```python
@sensor(job=ingestion_job)
def data_sensor(context):
    # Check for new files
    if new_files_found():
        yield RunRequest()
```

---

## Performance

### Execution Time

Typical pipeline execution:
- **Ingestion only**: 2-3 seconds
- **Complete pipeline**: 10-15 seconds

Breakdown:
- Ingestion (parallel): 2-3s
- Validation: 1-2s
- Preparation: 2-3s
- Features: 2-3s
- Training: 2-4s

### Optimization Tips

1. **Parallel Ingestion**: Already implemented
2. **Lazy Loading**: Load data only when needed
3. **Caching**: Use Dagster's output caching
4. **Batching**: Process in batches if data is large

---

## Deployment

### Local Development
```bash
dagster dev
```

### CI/CD Integration

GitHub Actions example:
```yaml
- name: Run Dagster Pipeline
  run: |
    pip install -r requirements.txt
    dagster job execute -f src/orchestration/dagster_pipeline.py -j complete_pipeline_job
```

### Docker (Advanced)

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["dagster", "dev"]
```

Run: `docker build -t recomart . && docker run -p 3000:3000 recomart`

---

## Logging

### Log Locations

1. **Console**: When running CLI/Python
2. **Web UI**: In Logs tab for each op
3. **Files**: `dagster_data/logs/`

### Log Levels

- `INFO`: Standard operations
- `WARNING`: Non-critical issues
- `ERROR`: Operation failures
- `DEBUG`: Detailed debugging info

---

## Testing

### Unit Test an Op

```python
from dagster import execute_op

def test_ingest_users_op():
    result = execute_op(ingest_users_op)
    assert result.success
    output = result.output_value()
    assert output['record_count'] > 0
```

Run tests:
```bash
pytest tests/
```

---

## Summary

**Dagster provides**:
✓ Visual pipeline monitoring
✓ Parallel op execution
✓ Built-in data observability
✓ Lightweight & easy to deploy
✓ Type-safe op definitions
✓ Beautiful web UI
✓ Production-ready features

**Next Steps**:
1. Start with `dagster dev`
2. Explore the web UI
3. Set up daily schedules
4. Integrate with CI/CD
5. Monitor production runs

---

## Resources

- **Docs**: `docs/DAGSTER_ORCHESTRATION.md`
- **Code**: `src/orchestration/dagster_pipeline.py`
- **Config**: `dagster.yaml`
- **Dagster Docs**: https://docs.dagster.io/
