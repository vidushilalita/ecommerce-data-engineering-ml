"""
Dagster Pipeline Orchestration for RecoMart Data Engineering and ML Training

This module orchestrates the complete data pipeline:
1. Data Ingestion (Users, Products, Transactions)
2. Data Validation
3. Data Preparation (Cleaning)
4. Feature Engineering
5. Model Training (Collaborative Filtering)

Lightweight, modern orchestration using Dagster with built-in observability.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from dagster import (
    job,
    op,
    In,
    Out,
    DynamicOut,
    DynamicOutput,
    graph,
    String,
    Field,
    config_mapping,
    resource,
    logger as dagster_logger,
    in_process_executor,
)
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ingestion.ingest_users import UserDataIngestion
from src.ingestion.ingest_products import ProductDataIngestion
from src.ingestion.ingest_transactions import TransactionDataIngestion
from src.validation.validate_data import DataValidator
from src.preparation.clean_data import DataPreparation
from src.features.engineer_features import FeatureEngineer
from src.model_training.collaborative_filtering import CollaborativeFilteringModel
from src.utils.storage import DataLakeStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ==================== RESOURCES ====================

@resource
def data_storage_resource(context):
    """Provides data lake storage instance"""
    return DataLakeStorage(base_path='storage')


# ==================== INGESTION OPS ====================

@op(
    description="Ingest user data from CSV files",
    tags={"type": "ingestion"}
)
def ingest_users_op(context) -> Dict[str, Any]:
    """
    Op: Ingest user data
    
    Reads CSV files containing 'user' in filename, merges them,
    cleans, and stores in data lake.
    """
    context.log.info("Starting user data ingestion...")
    
    try:
        ingestion = UserDataIngestion(data_dir='data', storage_base='storage')
        metadata = ingestion.ingest()
        
        context.log.info(
            f"User ingestion complete: {metadata['record_count']} records, "
            f"stored at {metadata['file_path']}"
        )
        
        return {
            'status': 'success',
            'record_count': metadata['record_count'],
            'file_path': metadata['file_path'],
            'source': 'users'
        }
    except Exception as e:
        context.log.error(f"User ingestion failed: {str(e)}")
        raise


@op(
    description="Ingest product data from JSON file",
    tags={"type": "ingestion"}
)
def ingest_products_op(context) -> Dict[str, Any]:
    """
    Op: Ingest product data
    
    Reads products.json, flattens JSON structures,
    validates, and stores in data lake.
    """
    context.log.info("Starting product data ingestion...")
    
    try:
        ingestion = ProductDataIngestion()
        metadata = ingestion.ingest()
        
        context.log.info(
            f"Product ingestion complete: {metadata['record_count']} records, "
            f"stored at {metadata['file_path']}"
        )
        
        return {
            'status': 'success',
            'record_count': metadata['record_count'],
            'file_path': metadata['file_path'],
            'source': 'products'
        }
    except Exception as e:
        context.log.error(f"Product ingestion failed: {str(e)}")
        raise


@op(
    description="Ingest transaction data from CSV files",
    tags={"type": "ingestion"}
)
def ingest_transactions_op(context) -> Dict[str, Any]:
    """
    Op: Ingest transaction data
    
    Reads CSV files containing 'transaction' in filename,
    parses timestamps, validates, and stores in data lake.
    """
    context.log.info("Starting transaction data ingestion...")
    
    try:
        ingestion = TransactionDataIngestion()
        metadata = ingestion.ingest()
        
        context.log.info(
            f"Transaction ingestion complete: {metadata['record_count']} records, "
            f"stored at {metadata['file_path']}"
        )
        
        return {
            'status': 'success',
            'record_count': metadata['record_count'],
            'file_path': metadata['file_path'],
            'source': 'transactions'
        }
    except Exception as e:
        context.log.error(f"Transaction ingestion failed: {str(e)}")
        raise


# ==================== VALIDATION OPS ====================

@op(
    description="Validate ingested data quality",
    ins={
        'users_metadata': In(),
        'products_metadata': In(),
        'transactions_metadata': In()
    },
    tags={"type": "validation"}
)
def validate_data_op(context, users_metadata, products_metadata, transactions_metadata) -> Dict[str, Any]:
    """
    Op: Validate data quality
    
    Runs comprehensive validation suite on ingested data,
    checks for completeness, correctness, and consistency.
    """
    context.log.info("Starting data validation...")
    
    try:
        validator = DataValidator()
        validation_results = validator.run_validation_suite()
        validator.save_validation_results(validation_results)
        
        quality_score = validation_results['overall']['quality_score']
        context.log.info(
            f"Data validation complete: Quality Score = {quality_score:.1%}"
        )
        
        return {
            'status': 'success',
            'quality_score': quality_score,
            'issues_found': len(validation_results['issues']),
            'validation_results': validation_results
        }
    except Exception as e:
        context.log.error(f"Data validation failed: {str(e)}")
        raise


# ==================== PREPARATION OPS ====================

@op(
    description="Clean and prepare data",
    ins={'validation_result': In()},
    tags={"type": "preparation"}
)
def prepare_data_op(context, validation_result) -> Dict[str, Any]:
    """
    Op: Prepare data
    
    Cleans users, products, and transactions:
    - Handles missing values
    - Encodes categorical variables
    - Normalizes numerical features
    - Removes duplicates
    """
    context.log.info("Starting data preparation...")
    
    try:
        prep = DataPreparation(storage_base='storage')
        users_df, products_df, transactions_df = prep.run_preparation_pipeline()
        
        context.log.info(
            f"Data preparation complete: "
            f"{len(users_df)} users, "
            f"{len(products_df)} products, "
            f"{len(transactions_df)} transactions"
        )
        
        return {
            'status': 'success',
            'users_count': len(users_df),
            'products_count': len(products_df),
            'transactions_count': len(transactions_df)
        }
    except Exception as e:
        context.log.error(f"Data preparation failed: {str(e)}")
        raise


# ==================== FEATURE ENGINEERING OPS ====================

@op(
    description="Create features for ML model",
    ins={'prep_result': In()},
    tags={"type": "features"}
)
def engineer_features_op(context, prep_result) -> Dict[str, Any]:
    """
    Op: Engineer features
    
    Creates features for recommendation system:
    - User features (activity, ratings, purchase ratio, category preference)
    - Item features (popularity, ratings, price tier, conversion rate)
    - Interaction features (implicit scores, recency weights)
    """
    context.log.info("Starting feature engineering...")
    
    try:
        engineer = FeatureEngineer(storage_base='storage')
        user_features, item_features, interaction_features = engineer.run_feature_engineering()
        
        context.log.info(
            f"Feature engineering complete: "
            f"{len(user_features)} user features, "
            f"{len(item_features)} item features, "
            f"{len(interaction_features)} interaction features"
        )
        
        return {
            'status': 'success',
            'user_features_count': len(user_features),
            'item_features_count': len(item_features),
            'interaction_features_count': len(interaction_features)
        }
    except Exception as e:
        context.log.error(f"Feature engineering failed: {str(e)}")
        raise


# ==================== MODEL TRAINING OPS ====================

@op(
    description="Train collaborative filtering model",
    ins={'features_result': In()},
    tags={"type": "model_training"}
)
def train_model_op(context, features_result) -> Dict[str, Any]:
    """
    Op: Train model
    
    Trains collaborative filtering model using SVD:
    - Loads interaction features
    - Prepares data for Surprise library
    - Trains SVD model with specified hyperparameters
    - Saves model to disk
    """
    context.log.info("Starting model training...")
    
    try:
        # Load interaction features
        storage = DataLakeStorage(base_path='storage')
        interactions_df = storage.load_latest('interaction_features', 'features')
        
        # Initialize and train model
        cf_model = CollaborativeFilteringModel(
            n_factors=50,
            n_epochs=20,
            lr_all=0.005,
            reg_all=0.02
        )
        
        # Prepare data
        dataset = cf_model.prepare_data(interactions_df)
        
        # Train
        trainset, testset = cf_model.train(dataset)
        
        # Save model
        models_dir = Path('models')
        models_dir.mkdir(exist_ok=True)
        model_path = models_dir / 'collaborative_filtering.pkl'
        cf_model.save_model(str(model_path))
        
        context.log.info(
            f"Model training complete: Model saved to {model_path}"
        )
        
        return {
            'status': 'success',
            'model_path': str(model_path),
            'training_records': len(trainset.all_ratings()),
            'test_records': len(testset)
        }
    except Exception as e:
        context.log.error(f"Model training failed: {str(e)}")
        raise


# ==================== GRAPH DEFINITION ====================

@graph
def recomart_etl_graph():
    """
    Define the data ingestion graph
    All ingestion ops run in parallel since they're independent
    """
    ingest_users_op()
    ingest_products_op()
    ingest_transactions_op()


@graph
def recomart_pipeline_graph():
    """
    Complete pipeline graph:
    1. Parallel data ingestion
    2. Data validation
    3. Data preparation
    4. Feature engineering
    5. Model training
    """
    # Step 1: Parallel ingestion
    users_meta = ingest_users_op()
    products_meta = ingest_products_op()
    transactions_meta = ingest_transactions_op()
    
    # Step 2: Validation (depends on all ingestion ops)
    validation_result = validate_data_op(
        users_metadata=users_meta,
        products_metadata=products_meta,
        transactions_metadata=transactions_meta
    )
    
    # Step 3: Preparation (depends on validation)
    prep_result = prepare_data_op(validation_result=validation_result)
    
    # Step 4: Feature Engineering (depends on preparation)
    features_result = engineer_features_op(prep_result=prep_result)
    
    # Step 5: Model Training (depends on features)
    model_result = train_model_op(features_result=features_result)
    
    return model_result


# ==================== JOB DEFINITIONS ====================

@job(
    name="recomart_ingestion_only",
    description="Run data ingestion pipeline only (ingestion ops in parallel)",
    tags={"pipeline": "ingestion"},
    executor_def=in_process_executor
)
def ingestion_job():
    """Job: Data Ingestion Only"""
    recomart_etl_graph()


@job(
    name="recomart_complete_pipeline",
    description="Run complete end-to-end pipeline (ingestion → validation → prep → features → training)",
    tags={"pipeline": "complete"},
    executor_def=in_process_executor
)
def complete_pipeline_job():
    """Job: Complete End-to-End Pipeline"""
    recomart_pipeline_graph()


# ==================== SENSOR OPS (Optional - Advanced) ====================

# Future enhancement: Add sensors for monitoring data freshness,
# data lake changes, etc.

if __name__ == "__main__":
    print("Dagster pipeline definitions loaded successfully")
    print("\nAvailable Jobs:")
    print("1. ingestion_job - Run data ingestion only")
    print("2. complete_pipeline_job - Run complete end-to-end pipeline")
