"""
Apache Airflow DAG: End-to-End Pipeline

Master DAG that orchestrates the complete RecoMart data pipeline:
1. Data Ingestion
2. Data Validation
3. Data Preparation
4. Feature Engineering
5. Feature Store Update
6. Model Training
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.python import PythonSensor
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
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 1, 22),
}

# Define DAG
dag = DAG(
    'recomart_end_to_end_pipeline',
    default_args=default_args,
    description='Complete RecoMart data pipeline',
    schedule_interval='@daily',
    catchup=False,
    tags=['end-to-end', 'production', 'data-pipeline'],
)

# Task functions
def run_ingest_users():
    """Run user data ingestion"""
    from src.ingestion.ingest_users import UserDataIngestion
    ingestion = UserDataIngestion()
    return ingestion.ingest()

def run_ingest_products():
    """Run product data ingestion"""
    from src.ingestion.ingest_products import ProductDataIngestion
    ingestion = ProductDataIngestion()
    return ingestion.ingest()

def run_ingest_transactions():
    """Run transaction data ingestion"""
    from src.ingestion.ingest_transactions import TransactionDataIngestion
    ingestion = TransactionDataIngestion()
    return ingestion.ingest()

def run_validation():
    """Run data validation"""
    from src.validation.validate_data import DataValidator
    validator = DataValidator()
    results = validator.run_validation_suite()
    validator.save_validation_results(results)
    
    # Check quality score
    if results['overall']['quality_score'] < 0.95:
        raise ValueError(f"Data quality score {results['overall']['quality_score']:.1%} below threshold 95%")
    
    return results

def run_preparation():
    """Run data preparation"""
    from src.preparation.clean_data import DataPreparation
    prep = DataPreparation()
    users, products, transactions = prep.run_preparation_pipeline()
    return len(users), len(products), len(transactions)

def run_feature_engineering():
    """Run feature engineering"""
    from src.features.engineer_features import FeatureEngineer
    engineer = FeatureEngineer()
    user_features, item_features, interaction_features = engineer.run_feature_engineering()
    return len(user_features), len(item_features), len(interaction_features)

def run_feature_store_update():
    """Update feature store"""
    from src.features.feature_store import SimpleFeatureStore, create_feature_metadata
    from src.utils.storage import DataLakeStorage
    
    storage = DataLakeStorage()
    user_features = storage.load_latest('user_features', 'features')
    item_features = storage.load_latest('item_features', 'features')
    
    feature_store = SimpleFeatureStore()
    feature_store.register_user_features(user_features)
    feature_store.register_item_features(item_features)
    
    metadata = create_feature_metadata()
    feature_store.register_feature_metadata(metadata)
    feature_store.close()
    
    return True

def run_model_training():
    """Train recommendation model"""
    from src.models.collaborative_filtering import CollaborativeFilteringModel
    from src.utils.storage import DataLakeStorage
    
    storage = DataLakeStorage()
    interactions_df = storage.load_latest('interaction_features', 'features')
    
    cf_model = CollaborativeFilteringModel()
    dataset = cf_model.prepare_data(interactions_df)
    trainset, testset = cf_model.train(dataset)
    
    # Save model
    model_dir = Path('models')
    model_dir.mkdir(exist_ok=True)
    cf_model.save_model(str(model_dir / 'collaborative_filtering.pkl'))
    
    return True

def run_batch_inference():
    """Run daily batch inference"""
    from src.inference.batch_inference import BatchInference
    inference = BatchInference()
    return inference.run_inference()

# Create tasks
task_ingest_users = PythonOperator(
    task_id='ingest_users',
    python_callable=run_ingest_users,
    dag=dag,
)

task_ingest_products = PythonOperator(
    task_id='ingest_products',
    python_callable=run_ingest_products,
    dag=dag,
)

task_ingest_transactions = PythonOperator(
    task_id='ingest_transactions',
    python_callable=run_ingest_transactions,
    dag=dag,
)

task_validation = PythonOperator(
    task_id='data_validation',
    python_callable=run_validation,
    dag=dag,
)

task_preparation = PythonOperator(
    task_id='data_preparation',
    python_callable=run_preparation,
    dag=dag,
)

task_feature_engineering = PythonOperator(
    task_id='feature_engineering',
    python_callable=run_feature_engineering,
    dag=dag,
)

task_feature_store = PythonOperator(
    task_id='update_feature_store',
    python_callable=run_feature_store_update,
    dag=dag,
)

task_model_training = PythonOperator(
    task_id='model_training',
    python_callable=run_model_training,
    dag=dag,
)

task_inference = PythonOperator(
    task_id='batch_inference',
    python_callable=run_batch_inference,
    dag=dag,
)

# Define dependencies
# 1. Parallel Ingestion -> Validation
[task_ingest_users, task_ingest_products, task_ingest_transactions] >> task_validation

# 2. Validation -> Prep -> FE -> Store -> Train -> Inference
task_validation >> task_preparation >> task_feature_engineering >> task_feature_store >> task_model_training >> task_inference
