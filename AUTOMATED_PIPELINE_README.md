# RecoMart Automated Data Pipeline - Complete Guide

## 🚀 Quick Start (2 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Pipeline
**Option A: Web UI (Recommended)**
```bash
dagster dev
# Open http://localhost:3000
# Click 'automated_pipeline_job'
# Click 'Materialize'
```

**Option B: Command Line**
```bash
python run_dagster_pipeline.py
```

**Option C: Windows Batch**
```bash
run_pipeline.bat ui
```

**Option D: Linux/macOS**
```bash
./run_pipeline.sh ui
```

---

## What is the Automated Pipeline?

The **automated pipeline** is a fully configurable, production-ready data engineering workflow that:

- ✅ **Runs Automatically** - Tasks execute in sequence, each waiting for the previous to complete
- ✅ **Configuration-Driven** - Control everything via `pipeline_config.yaml` (no code changes)
- ✅ **Smart Dependencies** - Tasks automatically wait for their dependencies
- ✅ **Real-time Monitoring** - Watch execution in the web UI with logs and metrics
- ✅ **Error Recovery** - Automatic retries with exponential backoff
- ✅ **Scheduling Support** - Run on a schedule (e.g., every morning at 2 AM)
- ✅ **Production-Ready** - Handles failures, timeouts, resource limits

### Pipeline Stages

```
1️⃣  INGESTION
    Load data from CSV/JSON files
    └─ Automatically waits for completion
    
2️⃣  VALIDATION
    Check data quality
    └─ Automatically waits for ingestion
    
3️⃣  PREPARATION
    Clean, normalize, and encode data
    └─ Automatically waits for validation
    
4️⃣  FEATURE ENGINEERING
    Create ML features
    └─ Automatically waits for preparation
    
5️⃣  MODEL TRAINING
    Train recommendation model
    └─ Automatically waits for features
```

---

## The Configuration File

**Location**: `pipeline_config.yaml`

This single YAML file controls EVERYTHING about your pipeline:

### What You Can Configure

```yaml
# Which tasks run
tasks:
  ingestion:
    enabled: true
    depends_on: []
    timeout_seconds: 300
    retry_count: 2

# When tasks should timeout
execution:
  timeout_seconds: 3600
  max_retries: 2
  continue_on_error: false

# Where data is stored
storage:
  base_dir: storage
  data_dir: data
  models_dir: models

# Automatic scheduling
scheduling:
  enabled: true
  cron: "0 2 * * *"  # 2 AM daily

# Error handling
retry_policy:
  use_exponential_backoff: true
  max_backoff: 300

# Resource limits
resources:
  max_memory_gb: 4
  max_cpu_cores: 2
```

### Example: Enable Only Certain Tasks

```yaml
tasks:
  ingestion:
    enabled: true          # ✓ Run this
  validation:
    enabled: false         # ✗ Skip this
  preparation:
    enabled: true          # ✓ Run this
  features:
    enabled: false         # ✗ Skip this
  training:
    enabled: false         # ✗ Skip this
```

### Example: Set Task Timeouts

```yaml
tasks:
  ingestion:
    timeout_seconds: 300       # 5 minutes for ingestion
  training:
    timeout_seconds: 900       # 15 minutes for training (slower)
```

### Example: Configure Retries

```yaml
tasks:
  ingestion:
    retry_count: 2             # Retry ingestion up to 2 times
  training:
    retry_count: 1             # Expensive - only retry once
```

---

## Running the Pipeline

### Method 1: Web UI (Recommended) ⭐

```bash
dagster dev
```

Then:
1. Open http://localhost:3000 in your browser
2. Click on **`automated_pipeline_job`** in the left sidebar
3. Click the **"Materialize"** button
4. Watch real-time execution with logs and metrics

**Benefits**:
- Visual pipeline DAG
- Real-time logs per task
- Click on tasks to see details
- View execution history
- Track performance metrics

---

### Method 2: Command Line

```bash
# Run automated pipeline
dagster job execute \
  -f src/orchestration/automated_pipeline.py \
  -j automated_pipeline_job

# Run with custom config
PIPELINE_CONFIG=custom_config.yaml dagster job execute \
  -f src/orchestration/automated_pipeline.py \
  -j automated_pipeline_job
```

---

### Method 3: Python Script

```bash
# Run with default config
python run_dagster_pipeline.py

# Run UI
python run_dagster_pipeline.py --ui

# Run specific job
python run_dagster_pipeline.py --ingestion-only
```

---

### Method 4: Interactive Menu

```bash
# Windows
run_pipeline.bat

# Linux/macOS
./run_pipeline.sh

# Or Python (any platform)
python dagster_quickstart.py
```

---

## Automatic Task Dependencies

The pipeline automatically manages task dependencies. You don't need to worry about ordering!

### How It Works

1. **Dependency Declaration** (in `pipeline_config.yaml`):
   ```yaml
   tasks:
     validation:
       depends_on: [ingestion]    # ← Says "wait for ingestion"
   ```

2. **Automatic Waiting**:
   - Validation task is created but doesn't start
   - Pipeline waits for ingestion to complete
   - Only when ingestion succeeds does validation start

3. **Sequential Execution**:
   ```
   TIME     EVENT
   ════════════════════════════════════════
   0:00s    ingestion_op starts
   0:30s    ingestion_op completes ✓
   0:30s    validation_op starts (auto-triggered)
   1:00s    validation_op completes ✓
   1:00s    preparation_op starts (auto-triggered)
   2:00s    preparation_op completes ✓
   2:00s    features_op starts (auto-triggered)
   3:00s    features_op completes ✓
   3:00s    training_op starts (auto-triggered)
   4:00s    training_op completes ✓
   4:00s    PIPELINE SUCCESS ✓
   ```

---

## Monitoring and Logs

### In the Web UI

The dashboard shows:

| Feature | Shows |
|---------|-------|
| **Task Status** | Running, success, failure, skipped |
| **Duration** | How long each task took |
| **Logs** | Real-time log output per task |
| **Record Counts** | How many records processed |
| **Data Quality** | Validation scores |
| **Errors** | What went wrong and why |

### Log Files

Logs are saved in multiple locations:

```
dagster_data/logs/          # Dagster execution logs
logs/pipeline.log           # Custom pipeline logs
```

---

## Scheduling Automated Runs

Run your pipeline automatically on a schedule!

### Step 1: Enable Scheduling in Config

Edit `pipeline_config.yaml`:

```yaml
scheduling:
  enabled: true
  cron: "0 2 * * *"      # 2 AM every day
  timezone: UTC
```

### Step 2: Start Dagster Daemon

Open **two terminal windows**:

**Terminal 1: Web UI**
```bash
dagster dev
```

**Terminal 2: Daemon** (keep running)
```bash
dagster daemon run
```

The daemon will execute your pipeline automatically at 2 AM every day!

### Cron Schedule Examples

| Cron | Description |
|------|-------------|
| `0 2 * * *` | Every day at 2 AM |
| `0 */2 * * *` | Every 2 hours |
| `0 9 * * MON` | Every Monday at 9 AM |
| `30 14 * * *` | Every day at 2:30 PM |
| `0 0 1 * *` | First day of month at midnight |

---

## Error Handling and Recovery

### Automatic Retries

If a task fails, it automatically retries:

```yaml
tasks:
  ingestion:
    retry_count: 2        # Retry up to 2 times
    retry_delay: 30       # Wait 30 seconds between retries
```

### Exponential Backoff

Retry delays increase exponentially:

```yaml
retry_policy:
  use_exponential_backoff: true
  backoff_base: 2         # Wait 2, 4, 8, 16... seconds
  max_backoff: 300        # Max 5 minute wait
```

### Skip Failed Tasks

```yaml
execution:
  continue_on_error: false  # ← Stop if any task fails
  # or:
  # continue_on_error: true # Skip failed task, continue
```

---

## Available Jobs

The pipeline comes with multiple job options:

### 1. `automated_pipeline_job` ⭐ (RECOMMENDED)

```bash
dagster job execute -f src/orchestration/automated_pipeline.py -j automated_pipeline_job
```

**Features**:
- Fully configurable via `pipeline_config.yaml`
- Automatic dependency management
- Complete pipeline (ingestion → training)
- Production-ready

---

### 2. `ingestion_only_job`

```bash
dagster job execute -f src/orchestration/automated_pipeline.py -j ingestion_only_job
```

**Use when**: You just want fresh data without processing

---

### 3. `validation_only_job`

```bash
dagster job execute -f src/orchestration/automated_pipeline.py -j validation_only_job
```

**Use when**: You want to run validation after ingestion

---

### Legacy Jobs

For backwards compatibility:
- `complete_pipeline_job` - Original hardcoded pipeline
- `ingestion_job` - Original ingestion-only job

---

## Advanced: Custom Configurations

### Use Different Configs for Different Environments

Create separate configuration files:

```bash
# Development
PIPELINE_CONFIG=pipeline_config.dev.yaml dagster dev

# Production
PIPELINE_CONFIG=pipeline_config.prod.yaml dagster dev
```

Example `pipeline_config.dev.yaml`:
```yaml
logging:
  level: DEBUG
execution:
  timeout_seconds: 1800    # 30 min timeout
tasks:
  training:
    timeout_seconds: 300   # Short timeout for testing
```

Example `pipeline_config.prod.yaml`:
```yaml
logging:
  level: WARNING
execution:
  timeout_seconds: 7200    # 2 hour timeout
tasks:
  training:
    timeout_seconds: 1800  # Longer timeout for production
```

---

### Task-Specific Hyperparameters

Configure model hyperparameters in the YAML:

```yaml
tasks:
  training:
    config:
      model_type: collaborative_filtering_svd
      svd:
        n_factors: 50      # Number of latent factors
        n_epochs: 20       # Training epochs
        learning_rate: 0.005
        regularization: 0.02
      train_test_split: 0.8
```

---

## Troubleshooting

### Pipeline Won't Start

**Check if dependencies are installed**:
```bash
pip install -r requirements.txt
```

**Check if Dagster is installed**:
```bash
python -m dagster --version
```

---

### Port 3000 Already in Use

```bash
# Use different port
dagster dev --port 3001

# Or kill the process
# Windows (PowerShell):
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
```

---

### Config File Not Found

**Make sure file exists**:
```bash
ls pipeline_config.yaml    # Linux/macOS
dir pipeline_config.yaml   # Windows
```

**Check default location**:
```python
from src.orchestration.config_driven_pipeline import PipelineConfig
config = PipelineConfig()  # Uses ./pipeline_config.yaml
```

---

### View Configuration

```bash
# Print configuration
python -c "from src.orchestration.config_driven_pipeline import PipelineConfig; import json; print(json.dumps(PipelineConfig().to_dict(), indent=2))"
```

---

### Debug Task Dependencies

```bash
# Print execution order
python -c "from src.orchestration.config_driven_pipeline import PipelineConfig, TaskDependencyGraph; g = TaskDependencyGraph(PipelineConfig()); print('Execution order:', g.get_execution_order())"

# Print parallel groups
python -c "from src.orchestration.config_driven_pipeline import PipelineConfig, TaskDependencyGraph; g = TaskDependencyGraph(PipelineConfig()); print('Parallel groups:', g.get_parallel_groups())"
```

---

## Production Deployment

### On-Premise Server

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start UI and daemon in background
nohup dagster dev &
nohup dagster daemon run &

# 3. Access at http://server:3000
```

### Docker Container

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["dagster", "dev"]
```

Run:
```bash
docker build -t recomart .
docker run -p 3000:3000 -v $(pwd)/pipeline_config.yaml:/app/pipeline_config.yaml recomart
```

### Kubernetes

Create `k8s-job.yaml`:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: recomart-pipeline
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: pipeline
            image: recomart:latest
            command: ["python", "run_dagster_pipeline.py"]
          restartPolicy: OnFailure
```

Deploy:
```bash
kubectl apply -f k8s-job.yaml
```

---

## Performance Tips

### Optimize Timeout Values

```yaml
tasks:
  ingestion:
    timeout_seconds: 300       # Realistic for your data size
  training:
    timeout_seconds: 900       # Training takes longer
```

### Parallel Execution

```yaml
execution:
  mode: parallel      # Independent tasks run together
```

### Resource Limits

```yaml
resources:
  max_memory_gb: 8           # Increase for large datasets
  max_cpu_cores: 4           # Increase for parallel processing
```

---

## File Structure

```
ecommerce-data-engineering-ml/
├── pipeline_config.yaml              ← Edit this to control pipeline!
├── src/
│   └── orchestration/
│       ├── automated_pipeline.py     ← Config-driven pipeline (RECOMMENDED)
│       ├── config_driven_pipeline.py ← Configuration classes
│       ├── dagster_pipeline.py       ← Original pipeline (deprecated)
│       └── repository.py             ← Jobs registry
├── docs/
│   ├── AUTOMATED_PIPELINE.md         ← Detailed guide
│   ├── DAGSTER_ORCHESTRATION.md      ← Original orchestration docs
│   └── DAGSTER_QUICKSTART.md         ← Quick reference
├── dagster_quickstart.py             ← Interactive menu
├── run_dagster_pipeline.py           ← Python runner
├── run_pipeline.bat                  ← Windows batch script
└── run_pipeline.sh                   ← Linux/macOS shell script
```

---

## Summary

**The Automated Pipeline provides**:

1. ✅ **Fully Configurable** - Edit YAML, no code changes
2. ✅ **Automatic Dependencies** - Tasks wait for each other
3. ✅ **Flexible Scheduling** - Run on demand or automatically
4. ✅ **Real-time Monitoring** - Watch execution in web UI
5. ✅ **Error Recovery** - Automatic retries with backoff
6. ✅ **Production-Ready** - Handles failures gracefully
7. ✅ **Easy to Deploy** - Works locally, Docker, Kubernetes

**To Get Started**:

1. **Start the UI**:
   ```bash
   dagster dev
   ```

2. **Edit config** (optional):
   ```
   vim pipeline_config.yaml
   ```

3. **Run the pipeline**:
   - Click `automated_pipeline_job` in web UI
   - Click "Materialize"
   - Watch it go!

4. **For scheduled runs**:
   ```yaml
   scheduling:
     enabled: true
     cron: "0 2 * * *"
   ```
   Then run: `dagster daemon run`

---

## Resources

- **Main Config**: `pipeline_config.yaml`
- **Code**: `src/orchestration/automated_pipeline.py`
- **Guide**: `docs/AUTOMATED_PIPELINE.md`
- **Dagster**: https://docs.dagster.io/

Happy automating! 🚀
