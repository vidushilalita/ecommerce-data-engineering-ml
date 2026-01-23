# Apache Airflow Setup Guide for Windows

## Overview

This guide covers setting up Apache Airflow locally on Windows for the RecoMart data pipeline.

## Prerequisites

- Python 3.8+
- pip
- Virtual environment activated

## Installation

### 1. Set Airflow Home

```powershell
# Set environment variable for Airflow home
$env:AIRFLOW_HOME = "C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml\airflow"

# Make it permanent
[System.Environment]::SetEnvironmentVariable('AIRFLOW_HOME', $env:AIRFLOW_HOME, 'User')
```

### 2. Install Airflow

```bash
# Install Airflow with constraints for Python 3.8
pip install "apache-airflow==2.10.4" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.8.txt"
```

### 3. Initialize Database

```bash
# Initialize Airflow database (SQLite by default)
airflow db init
```

### 4. Create Admin User

```bash
# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@recomart.com \
    --password admin123
```

### 5. Configure Airflow

Edit `airflow/airflow.cfg`:

```ini
[core]
dags_folder = C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml\airflow\dags
base_log_folder = C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml\airflow\logs
executor = LocalExecutor
load_examples = False

[webserver]
web_server_port = 8080
base_url = http://localhost:8080

[scheduler]
dag_dir_list_interval = 60
```

## Running Airflow

### Start Webserver (Terminal 1)

```bash
airflow webserver --port 8080
```

### Start Scheduler (Terminal 2)

```bash
airflow scheduler
```

### Access Web UI

Open browser: http://localhost:8080
- Username: admin
- Password: admin123

## DAGs in RecoMart

### 1. data_ingestion
- **Schedule**: Daily
- **Tasks**: Ingest users, products, transactions
- **Execution**: Parallel

### 2. recomart_end_to_end_pipeline
- **Schedule**: Daily
- **Tasks**: Complete pipeline (ingestion → validation → preparation → features → model)
- **Execution**: Sequential with dependencies

## Testing DAGs

### List DAGs

```bash
airflow dags list
```

### Test Specific Task

```bash
# Test task without running dependencies
airflow tasks test recomart_end_to_end_pipeline data_ingestion 2026-01-22
```

### Run DAG

```bash
# Trigger DAG manually
airflow dags trigger recomart_end_to_end_pipeline

# Run with execution date
airflow dags backfill recomart_end_to_end_pipeline --start-date 2026-01-22 --end-date 2026-01-22
```

## Monitoring

### Check Task Status

```bash
# List task instances
airflow tasks list recomart_end_to_end_pipeline
```

### View Logs

```bash
# Tail logs
tail -f airflow/logs/scheduler/latest/*.log
```

### Web UI Features

- **DAG View**: Visualize task dependencies
- **Tree View**: See execution history
- **Graph View**: Task relationships
- **Gantt Chart**: Task duration and overlap
- **Task Logs**: Detailed execution logs

## Troubleshooting

### Issue: Import errors in DAGs

**Solution**: Ensure project root is in Python path
```python
sys.path.append(str(Path(__file__).parent.parent.parent))
```

### Issue: Webserver won't start

**Solution**:
```bash
# Kill existing processes
taskkill /F /IM airflow.exe

# Remove PID file
Remove-Item -Path "$env:AIRFLOW_HOME/airflow-webserver.pid"
```

### Issue: DAGs not showing in UI

**Solution**:
1. Check DAG files for syntax errors
2. Refresh DAGs: Click "Refresh" button in UI
3. Check `dag_dir_list_interval` in config

### Issue: Tasks fail silently

**Solution**:
- Check task logs in UI
- Run task test command
- Verify dependencies installed

## Best Practices

1. **Error Handling**: Use retries and email alerts
2. **Logging**: Log important events in tasks
3. **Idempotency**: Ensure tasks can be rerun safely
4. **Testing**: Test tasks individually before DAG
5. **Monitoring**: Set up email/Slack notifications
6. **Documentation**: Document DAG purpose and schedule

## Configuration for Production

For production deployment:

1. **Use PostgreSQL**: Replace SQLite
```ini
[database]
sql_alchemy_conn = postgresql+psycopg2://user:password@localhost/airflow
```

2. **Use CeleryExecutor**: For distributed execution
```ini
[core]
executor = CeleryExecutor
```

3. **Set up Redis**: For task queue
```ini
[celery]
broker_url = redis://localhost:6379/0
result_backend = db+postgresql://user:password@localhost/airflow
```

4. **Configure Secrets**: Use Airflow Variables/Connections
```bash
airflow variables set DATA_PATH /path/to/data
airflow connections add 'my_db' --conn-type postgres --conn-host localhost
```

## Useful Commands

```bash
# Pause/unpause DAG
airflow dags pause recomart_end_to_end_pipeline
airflow dags unpause recomart_end_to_end_pipeline

# Clear task instances
airflow tasks clear recomart_end_to_end_pipeline

# Show DAG structure
airflow dags show recomart_end_to_end_pipeline

# Validate DAG
python airflow/dags/dag_end_to_end.py
```

## Resources

- [Airflow Documentation](https://airflow.apache.org/docs/)
- [Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Troubleshooting](https://airflow.apache.org/docs/apache-airflow/stable/troubleshooting.html)
