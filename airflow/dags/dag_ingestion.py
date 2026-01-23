"""
Apache Airflow DAG: Data Ingestion

Orchestrates data ingestion from all sources (users, products, transactions)
with error handling, retries, and email alerts.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Default arguments
default_args = {
    'owner': 'data-platform-team',
    'depends_on_past': False,
    'email': ['data-team@recomart.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 1, 22),
}

# Define DAG
dag = DAG(
    'data_ingestion',
    default_args=default_args,
    description='Ingest data from all sources',
    schedule_interval='@daily',  # Run daily at midnight
    catchup=False,
    tags=['ingestion', 'data-pipeline'],
)

# Define tasks
def ingest_users():
    """Ingest user data"""
    from src.ingestion.ingest_users import UserDataIngestion
    ingestion = UserDataIngestion()
    return ingestion.ingest()

def ingest_products():
    """Ingest product data"""
    from src.ingestion.ingest_products import ProductDataIngestion
    ingestion = ProductDataIngestion()
    return ingestion.ingest()

def ingest_transactions():
    """Ingest transaction data"""
    from src.ingestion.ingest_transactions import TransactionDataIngestion
    ingestion = TransactionDataIngestion()
    return ingestion.ingest()

# Create tasks
task_ingest_users = PythonOperator(
    task_id='ingest_users',
    python_callable=ingest_users,
    dag=dag,
)

task_ingest_products = PythonOperator(
    task_id='ingest_products',
    python_callable=ingest_products,
    dag=dag,
)

task_ingest_transactions = PythonOperator(
    task_id='ingest_transactions',
    python_callable=ingest_transactions,
    dag=dag,
)

# Tasks can run in parallel
[task_ingest_users, task_ingest_products, task_ingest_transactions]
