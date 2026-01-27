# Automated Configuration-Driven Pipeline Guide

## Overview

The RecoMart pipeline now supports **fully automated, configuration-driven execution** using **Dagster**. All pipeline behavior is controlled through `pipeline_config.yaml` without modifying code.

### Key Features

✅ **Automatic Dependency Management** - Tasks wait for their dependencies to complete
✅ **Configuration File Control** - Edit `pipeline_config.yaml` to customize behavior
✅ **No Code Changes** - Control everything from YAML
✅ **Flexible Scheduling** - Enable automated runs on a schedule
✅ **Comprehensive Logging** - Detailed logs for every task
✅ **Error Recovery** - Configurable retry logic with exponential backoff
✅ **Real-time Monitoring** - Watch execution in Dagster web UI

---

## Quick Start (3 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Web UI
```bash
dagster dev
```

### 3. Execute Pipeline
- Open http://localhost:3000
- Click `automated_pipeline_job` (⭐ recommended)
- Click "Materialize" button
- Watch it run!

---

## Pipeline Configuration File

**Location**: `pipeline_config.yaml`

This single file controls EVERYTHING:
- Which tasks run
- Task dependencies
- Timeouts and retries
- Logging levels
- Scheduling
- Resource limits
- And much more

### Main Sections

```yaml
pipeline:           # Pipeline metadata
execution:          # Execution settings (timeouts, retries)
storage:            # Where data is stored
tasks:              # Task configuration (most important!)
logging:            # Logging configuration
scheduling:         # Automated schedule (optional)
notifications:      # Email/Slack alerts (optional)
monitoring:         # Performance monitoring
retry_policy:       # Retry behavior
resources:          # Resource limits
```

---

## Task Dependency Management

### Automatic Dependency Waiting

Each task automatically waits for its dependencies to complete:

```yaml
tasks:
  ingestion:
    enabled: true
    depends_on: []              # ← No dependencies (runs first)
    
  validation:
    enabled: true
    depends_on: [ingestion]     # ← Waits for ingestion to complete
    
  preparation:
    enabled: true
    depends_on: [validation]    # ← Waits for validation to complete
    
  features:
    enabled: true
    depends_on: [preparation]   # ← Waits for preparation to complete
    
  training:
    enabled: true
    depends_on: [features]      # ← Waits for features to complete
```

### Execution Flow

```
START
  │
  ├─→ ingestion (start immediately)
  │     │
  │     └─→ [waits for completion]
  │
  ├─→ validation (automatically waits for ingestion)
  │     │
  │     └─→ [waits for completion]
  │
  ├─→ preparation (automatically waits for validation)
  │     │
  │     └─→ [waits for completion]
  │
  ├─→ features (automatically waits for preparation)
  │     │
  │     └─→ [waits for completion]
  │
  ├─→ training (automatically waits for features)
  │     │
  │     └─→ [waits for completion]
  │
  └─→ END (all tasks complete)
```

---

## Configuring Tasks

### Example: Enable/Disable Tasks

```yaml
tasks:
  ingestion:
    enabled: true      # ✓ This task will run
  
  validation:
    enabled: false     # ✗ This task will be skipped
  
  training:
    enabled: true      # ✓ This task will run
```

The pipeline will skip disabled tasks and their dependents.

---

### Example: Set Task Timeouts

```yaml
tasks:
  ingestion:
    timeout_seconds: 300      # 5 minutes
    
  training:
    timeout_seconds: 900      # 15 minutes (training is slower)
```

If a task exceeds its timeout, it will be retried (if retries are available).

---

### Example: Configure Retries

```yaml
tasks:
  ingestion:
    retry_count: 2            # Retry up to 2 times on failure
    retry_delay: 30           # Wait 30 seconds between retries
  
  training:
    retry_count: 1            # Expensive task - only retry once
```

---

### Example: Task-Specific Configuration

```yaml
tasks:
  training:
    config:
      model_type: collaborative_filtering_svd
      
      # SVD hyperparameters
      svd:
        n_factors: 50
        n_epochs: 20
        learning_rate: 0.005
        regularization: 0.02
      
      # Train/test split
      train_test_split: 0.8
      
      # Model output settings
      save_model: true
      model_format: pickle
      model_name: collaborative_filtering
```

---

## Running Automated Pipelines

### Option 1: Web UI (Recommended)

```bash
dagster dev
```

Then:
1. Open http://localhost:3000
2. Click `automated_pipeline_job`
3. Click "Materialize"
4. Watch execution in real-time

**Advantages**:
- Visual feedback
- Real-time logs
- Click to see task details
- Monitor progress

---

### Option 2: Command Line

```bash
# Run the automated pipeline
dagster job execute \
  -f src/orchestration/automated_pipeline.py \
  -j automated_pipeline_job
```

---

### Option 3: Python Script

```bash
python run_dagster_pipeline.py
```

Or directly:

```python
from src.orchestration.automated_pipeline import execute_pipeline_programmatically

success = execute_pipeline_programmatically()
```

---

### Option 4: Use Custom Config

Run with a different configuration file:

```python
from src.orchestration.config_driven_pipeline import PipelineConfig
from src.orchestration.automated_pipeline import automated_pipeline_job
from dagster import execute_job, DagsterInstance

# Load custom config
config = PipelineConfig('custom_pipeline_config.yaml')

# Execute job
instance = DagsterInstance.ephemeral()
result = execute_job(automated_pipeline_job, instance=instance)
```

---

## Scheduling Automated Runs

Enable scheduled execution so the pipeline runs automatically:

### Step 1: Edit `pipeline_config.yaml`

```yaml
scheduling:
  enabled: true                    # Enable scheduling
  cron: "0 2 * * *"               # 2 AM every day
  timezone: UTC
  run_on_startup: false            # Don't run at startup
```

### Step 2: Use Dagster Daemon

```bash
# Terminal 1: Start Dagster UI
dagster dev

# Terminal 2: Start Dagster daemon (separate terminal)
dagster daemon run
```

The pipeline will now execute automatically according to the schedule!

### Cron Schedule Examples

| Schedule | Description |
|----------|-------------|
| `0 2 * * *` | Every day at 2 AM |
| `0 */2 * * *` | Every 2 hours |
| `0 9 * * MON` | Every Monday at 9 AM |
| `0 0 1 * *` | First day of every month at midnight |
| `0 * * * *` | Every hour |

---

## Monitoring and Observability

### Real-time Monitoring

The web UI shows:
- **Task Status**: Running, success, failure, skipped
- **Duration**: How long each task took
- **Logs**: Real-time log output per task
- **Data**: Record counts and quality metrics
- **History**: Past executions

### Logs Location

```
dagster_data/logs/              # All Dagster logs
logs/pipeline.log               # Custom pipeline logs
```

### Performance Tracking

Set thresholds for slow tasks:

```yaml
monitoring:
  performance:
    slow_task_threshold_seconds: 300  # Warn if task > 5 min
```

---

## Error Handling and Recovery

### Retry Configuration

```yaml
retry_policy:
  use_exponential_backoff: true
  backoff_base: 2              # Wait 2, 4, 8, 16... seconds
  max_backoff: 300             # Max 5 minutes between retries
  
  retry_on_errors:
    - timeout
    - connection_error
    - memory_error
  
  no_retry_on:
    - file_not_found
    - schema_error
    - validation_error
```

### Skip Failed Tasks

```yaml
execution:
  continue_on_error: false     # Stop if any task fails
  # or:
  # continue_on_error: true    # Skip failed tasks, continue
```

---

## Advanced: Multiple Configuration Files

Use different configs for different environments:

```bash
# Development
export PIPELINE_CONFIG=pipeline_config.dev.yaml
dagster dev

# Production
export PIPELINE_CONFIG=pipeline_config.prod.yaml
dagster dev
```

Create separate files:

```yaml
# pipeline_config.dev.yaml
logging:
  level: DEBUG

tasks:
  training:
    timeout_seconds: 300  # Short timeout for dev
```

```yaml
# pipeline_config.prod.yaml
logging:
  level: WARNING

tasks:
  training:
    timeout_seconds: 3600  # Longer timeout for prod
```

---

## Advanced: Notifications

Get alerts when pipeline completes or fails:

### Email Notifications

```yaml
notifications:
  enabled: true
  
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    sender: pipeline@example.com
    recipients:
      - admin@example.com
    notify_success: true
    notify_failure: true
```

### Slack Notifications

```yaml
notifications:
  enabled: true
  
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    channel: "#pipeline-alerts"
    notify_success: false
    notify_failure: true
```

---

## Performance Optimization

### Parallel vs Sequential Execution

```yaml
execution:
  mode: sequential    # One task at a time
  # or:
  # mode: parallel   # Independent tasks run together
```

### Resource Limits

```yaml
resources:
  max_memory_gb: 4           # Max 4 GB per task
  max_cpu_cores: 2           # Max 2 CPU cores
  max_disk_gb: 10            # Max 10 GB temp disk
```

### Execution Timeout

```yaml
execution:
  timeout_seconds: 3600      # Total pipeline timeout (1 hour)
```

---

## Troubleshooting

### Check Configuration

```bash
# View current configuration
python -c "from src.orchestration.config_driven_pipeline import PipelineConfig; c = PipelineConfig(); print(c.to_dict())"
```

### Validate Configuration

```python
from src.orchestration.config_driven_pipeline import PipelineConfig, TaskDependencyGraph

config = PipelineConfig()
graph = TaskDependencyGraph(config)

# Check execution order
print("Execution order:", graph.get_execution_order())

# Check parallel groups
print("Parallel groups:", graph.get_parallel_groups())
```

### View Task Information

```python
from src.orchestration.config_driven_pipeline import PipelineConfig, TaskDependencyGraph

config = PipelineConfig()
graph = TaskDependencyGraph(config)

# Get info about a specific task
info = graph.get_task_info('training')
print(f"Task: {info['name']}")
print(f"Depends on: {info['dependencies']}")
print(f"Timeout: {info['timeout']}s")
print(f"Retries: {info['retry_count']}")
```

---

## Pipeline Status Codes

### Task Status

| Status | Meaning | Action |
|--------|---------|--------|
| PENDING | Waiting for dependencies | Wait |
| RUNNING | Currently executing | Monitor logs |
| SUCCESS | Completed successfully | Next task starts |
| FAILURE | Failed (will retry) | Check logs |
| SKIPPED | Disabled in config | Next task skipped |
| TIMEOUT | Exceeded timeout limit | Retried or failed |

---

## Example: Custom Pipeline

Here's an example of customizing the pipeline for your needs:

```yaml
# Use only ingestion and validation (skip training)
pipeline:
  name: quick_data_check
  enabled: true

tasks:
  ingestion:
    enabled: true
    timeout_seconds: 300
  
  validation:
    enabled: true
    depends_on: [ingestion]
    timeout_seconds: 600
  
  preparation:
    enabled: false    # Skip this
  
  features:
    enabled: false    # Skip this
  
  training:
    enabled: false    # Skip this

# Run immediately, once per day
scheduling:
  enabled: true
  cron: "0 1 * * *"   # 1 AM daily
```

---

## Example: Production Configuration

```yaml
pipeline:
  name: production_pipeline
  enabled: true

execution:
  mode: sequential
  timeout_seconds: 7200    # 2 hours max
  max_retries: 3
  continue_on_error: false

tasks:
  ingestion:
    enabled: true
    timeout_seconds: 600
    retry_count: 3
  
  validation:
    enabled: true
    depends_on: [ingestion]
    timeout_seconds: 1200
    retry_count: 2
  
  preparation:
    enabled: true
    depends_on: [validation]
    timeout_seconds: 1200
    retry_count: 2
  
  features:
    enabled: true
    depends_on: [preparation]
    timeout_seconds: 1200
    retry_count: 1
  
  training:
    enabled: true
    depends_on: [features]
    timeout_seconds: 1800   # 30 min for training
    retry_count: 1

logging:
  level: WARNING
  file: logs/production.log

scheduling:
  enabled: true
  cron: "0 2 * * *"       # 2 AM daily
  timezone: UTC

notifications:
  enabled: true
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/..."
    notify_failure: true

resources:
  max_memory_gb: 8
  max_cpu_cores: 4
```

---

## Summary

**Fully Automated Pipeline Benefits**:

1. ✅ **Config-Driven**: All settings in YAML, no code changes
2. ✅ **Automatic Dependencies**: Tasks wait for dependencies
3. ✅ **Flexible Scheduling**: Run on schedule or manually
4. ✅ **Comprehensive Logging**: Debug any issue
5. ✅ **Error Recovery**: Automatic retries with backoff
6. ✅ **Monitoring**: Real-time status in web UI
7. ✅ **Production-Ready**: Handles failures gracefully

**To Get Started**:
1. Edit `pipeline_config.yaml` to your needs
2. Run `dagster dev`
3. Click "Materialize" on `automated_pipeline_job`
4. Watch it go!

**For Scheduled Runs**:
1. Set `scheduling.enabled: true` in config
2. Run `dagster daemon run` in another terminal
3. Pipeline runs automatically on schedule!

---

## Resources

- **Configuration File**: `pipeline_config.yaml`
- **Code**: `src/orchestration/automated_pipeline.py`
- **Config Classes**: `src/orchestration/config_driven_pipeline.py`
- **Dagster Docs**: https://docs.dagster.io/
