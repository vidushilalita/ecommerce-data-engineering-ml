"""
Dagster Repository Configuration

Defines the repository containing all Dagster pipelines and resources.
This file is the entry point for Dagster daemon and web UI.

Available Pipelines:
1. automated_pipeline_job - Fully automated, config-driven pipeline (RECOMMENDED)
2. ingestion_only_job - Run only data ingestion
3. validation_only_job - Run validation task
4. feature_engineering_job - Run data preparation and feature engineering
5. model_training_job - Run model training only
"""

from dagster import repository
from src.orchestration.automated_pipeline import (
    automated_pipeline_job,
    ingestion_only_job,
    validation_only_job,
    feature_engineering_job,
    model_training_job
)


@repository
def recomart_repository():
    """
    Main repository for RecoMart data pipeline
    
    Contains config-driven pipeline options:
    
    RECOMMENDED:
    - automated_pipeline_job: Fully configurable via pipeline_config.yaml
      Tasks automatically wait for dependencies. All settings in YAML.
    
    ALTERNATIVES:
    - ingestion_only_job: Run ingestion only (config-driven)
    - validation_only_job: Run validation only (config-driven)
    - feature_engineering_job: Run preparation & features (config-driven)
    - model_training_job: Run model training only (config-driven)
    """
    return [
        automated_pipeline_job,      #  Recommended - config-driven
        ingestion_only_job,
        validation_only_job,
        feature_engineering_job,
        model_training_job,
    ]


if __name__ == "__main__":
    print("RecoMart Dagster Repository loaded")
    print("\nAvailable Jobs:")
    print(" automated_pipeline_job - Fully automated (config-driven)")
    print("  ingestion_only_job")
    print("  validation_only_job")
    print("  model_training_job")
    print("\nStart UI: dagster dev")
    print("Start automated pipeline: python run_dagster_pipeline.py")
