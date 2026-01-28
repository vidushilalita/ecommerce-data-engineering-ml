"""
Dagster Repository Configuration

Defines the repository containing all Dagster pipelines and resources.
This file is the entry point for Dagster daemon and web UI.

Available Pipelines:
1. automated_pipeline_job - Fully automated, config-driven pipeline (RECOMMENDED)
2. ingestion_only_job - Run only data ingestion
3. validation_only_job - Run validation task
4. complete_pipeline_job - Original hardcoded pipeline
5. ingestion_job - Original ingestion-only pipeline
"""

from dagster import repository
from src.orchestration.dagster_pipeline import (
    ingestion_job,
    complete_pipeline_job
)
from src.orchestration.automated_pipeline import (
    automated_pipeline_job,
    ingestion_only_job,
    validation_only_job
)


@repository
def recomart_repository():
    """
    Main repository for RecoMart data pipeline
    
    Contains multiple pipeline options:
    
    RECOMMENDED:
    - automated_pipeline_job: Fully configurable via pipeline_config.yaml
      Tasks automatically wait for dependencies. All settings in YAML.
    
    ALTERNATIVES:
    - ingestion_only_job: Run ingestion only (config-driven)
    - validation_only_job: Run validation only (config-driven)
    - complete_pipeline_job: Traditional hardcoded pipeline
    - ingestion_job: Original ingestion-only job
    """
    return [
        automated_pipeline_job,      # ⭐ Recommended - config-driven
        ingestion_only_job,
        validation_only_job,
        complete_pipeline_job,
        ingestion_job,
    ]


if __name__ == "__main__":
    print("RecoMart Dagster Repository loaded")
    print("\nAvailable Jobs:")
    print("  ⭐ automated_pipeline_job - Fully automated (config-driven)")
    print("  ingestion_only_job")
    print("  validation_only_job")
    print("  complete_pipeline_job")
    print("  ingestion_job")
    print("\nStart UI: dagster dev")
    print("Start automated pipeline: python run_dagster_pipeline.py")
